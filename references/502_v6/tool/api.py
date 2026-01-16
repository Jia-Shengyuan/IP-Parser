from flask import Flask, request
from flask_restx import Api, Resource, fields
import os
from pathlib import Path
import re
import zipfile
import io
import base64

from core.variable import Variable, Scope
from core.function_unit import FunctionUnit
from core.system_context import SystemContext
from parser import process_c_file  # 请确保路径正确

app = Flask(__name__)
api = Api(app, version='1.0', title='File Analyzer API',
          description='Analyze C files in a directory')

ns = api.namespace('files', description='File analysis operations')

# 输入模型
path_model = api.model('PathModel', {
    'path': fields.String(required=True, description='Root folder path')
})

# 输出模型（通用格式）
analysis_model = api.model('FileAnalysis', {
    'file': fields.String(description='File name'),
    'function_name': fields.String(description='Main function name'),
    'analysis': fields.Raw(description='Analysis result')
})

files_model = api.model('FilesResult', {
    'files': fields.List(fields.Nested(analysis_model)),
    "zip_file": fields.String(description="Base64 encoded ZIP file")  # ### NEW
})


def list_ip_header_names(folder: str):
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError("Not a directory")

    pattern = re.compile(r"^IP_(.+)\.h$")
    result = []
    for p in folder.rglob("*.h"):
        match = pattern.match(p.name)
        if match:
            result.append(match.group(1))
    return result


### NEW — 创建 ZIP 文件并返回 Base64 字符串
def create_zip_base64(folder: Path):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in folder.rglob("*"):
            if f.is_file():
                zipf.write(f, f.relative_to(folder))

    zip_buffer.seek(0)
    return base64.b64encode(zip_buffer.read()).decode("utf-8")


@ns.route('/list')
class FileList(Resource):

    @ns.expect(path_model)
    @ns.marshal_with(files_model)
    def post(self):
        data = request.json
        folder = data.get("path")

        if not folder:
            api.abort(400, "Missing path")
        if not os.path.exists(folder):
            api.abort(404, "Path does not exist")
        folder = Path(folder)
        if not folder.is_dir():
            api.abort(400, "Not a directory")

        header_names = list_ip_header_names(folder)

        demo_content_map = {}
        for demo_file in folder.rglob("IP_*_Demo.c"):
            name = demo_file.name.replace("IP_", "").replace("_Demo.c", "")
            with open(demo_file, "r", encoding="utf-8") as f:
                demo_content_map[name] = f.read()

        output = []

        # 遍历非 Demo C 文件
        for cfile in folder.rglob("IP_*.c"):
            if cfile.name.endswith("_Demo.c"):
                continue

            file_ctx = SystemContext()
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # file_ctx.dump()
            process_c_file(str(cfile), file_ctx)
            file_ctx.run_analysis_pipeline()
            res = file_ctx.classify_interfaces()

            filtered_funcs = {fname: var_dict for fname, var_dict in res.items() if fname in header_names}

            analysis_list = []
            main_func_name = None
            # file_ctx.dump()
            for func_name, var_dict in filtered_funcs.items():
                func = file_ctx.functions.get(func_name)

                main_func_name = func_name
                analysis_list.append({
                    "api": func.api if func else "",
                    "list": {
                        # "param": [{"name": v.name, "type": v.type} for v in func.params] if func else [],
                        "param": [{"name": v.name, "type": v.type} for v in var_dict.get("param_vars", [])],
                        "in": [{"name": v.name, "type": v.type} for v in var_dict.get("in_vars", [])],
                        "out": [{"name": v.name, "type": v.type} for v in var_dict.get("out", [])],
                        "inout": [{"name": v.name, "type": v.type} for v in var_dict.get("inout_vars", [])],
                        "state": [{"name": v.name, "type": v.type} for v in var_dict.get("state_vars", [])]
                    },
                    "demo": demo_content_map.get(func_name, "")
                })

            output.append({
                "file": str(cfile),
                "function_name": main_func_name,
                "analysis": analysis_list if analysis_list else None
            })

        ### NEW — 把整个目录打包 zip 并作为 base64 放入返回值
        zip_b64 = create_zip_base64(folder)

        return {
            "files": output,
            "zip_file": zip_b64    # 新增字段
        }


if __name__ == "__main__":
    app.run(debug=True)

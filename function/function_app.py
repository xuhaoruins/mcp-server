import azure.functions as func
import logging
import re  # Added for regex

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Retrieve the Chinese string from key "text"
    text = req.params.get('text')
    if not text:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            text = req_body.get('text')

    if text:
        # Count Chinese characters using regex range \u4e00-\u9fff
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        count = len(chinese_chars)
        return func.HttpResponse(f"这段中文的字数是: {count}个字")
    else:
        return func.HttpResponse(
             "抱歉，无法计算。",
             status_code=200
        )
import json

from flask import Flask, request
from flask_cors import CORS

from core.processor import Recommender

app = Flask(__name__)
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/process-comment', methods=['POST'])
def process_comment():
    data = request.json
    comment = data.get('comment', '')
    tags = data.get('tags', [])
    settings = data.get('settings', {})

    google_cfg = {
        "api_key": settings.get("google_api_key"),
        "cse_id": settings.get("google_cse_key")
    }
    youtube_cfg = {
        "api_key": settings.get("youtube_api_key")
    }

    recommender = Recommender(google_cfg=google_cfg, youtube_cfg=youtube_cfg)
    response_data = recommender.process(data)
    return json.dumps({"response": response_data})

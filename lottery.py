from flask import Flask, request
import requests
import json
import random
from urllib.parse import urlparse

app = Flask(__name__)

urlApi = 'https://graphql-gateway-z5giai34ua-uc.a.run.app/'

def get_post_id(url):
    parsed = urlparse(url)
    postId = parsed.path.split('/')[-1]
    return postId

def fetch_token():
    response = requests.get('https://freshcut.gg/api/auth/anonymous-token')
    token = response.json()['token']
    return token

def get_comments(postId, token, offset=None):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    query = """
        query($userId: String!, $postId: ID!) {
            communities(userId: $userId) {
                post(input: { postId: $postId }) {
                    comments(limit: 50""" + (f", offset: {offset}" if offset else "") + """) {
                        id
                        content
                        author {
                            id
                            username
                        }
                    }
                }
            }
        }
    """
    variables = {
        "userId": "comment-lottery",
        "postId": postId
    }
    payload = {
        "query": query,
        "variables": variables
    }
    response = requests.post(urlApi, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception("Request failed with status code %d" % response.status_code)
    data = response.json()
    if 'errors' in data:
        print(data['errors'])
        return []
    comments = data['data']['communities']['post']['comments']
    return comments

def get_commenters(postId, token):
    comments = get_comments(postId, token)
    offset = 50
    while True:
        more_comments = get_comments(postId, token, offset)
        if not more_comments:
            break
        comments.extend(more_comments)
        offset += 50
    usernames = [comment['author']['username'] for comment in comments]
    uniqueusers = list(set(usernames))
    return uniqueusers

@app.route('/lottery', methods=['GET'])
def winner():
    url = request.args.get('url')
    winners_count = int(request.args.get('winners', 1))

    postId = get_post_id(url)
    token = fetch_token()
    eligibles = get_commenters(postId, token)
    winners = random.sample(eligibles, min(len(eligibles), winners_count))

    winner_profiles = [f"https://freshcut.gg/@{username}" for username in winners]

    return {"data": {"winners": winner_profiles}}

if __name__ == '__main__':
    app.run(debug=False)

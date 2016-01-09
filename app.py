#!flask/bin/python
import redis
import os
from flask import abort, Flask, jsonify, make_response, request

app = Flask(__name__)

@app.before_request
def enforce_ipwhitelist():
    # if IP whitelist supplied then apply it
    if "IPWHITELIST" in os.environ:
        if not request.remote_addr in os.environ['IPWHITELIST'].split():
            abort(403)

@app.before_request
def enforce_secret():
    # if secret required then make sure it's correct
    if "SECRET" in os.environ:
        if not request.json or not 'secret' in request.json:
            abort(403)
        if os.environ['SECRET'] != request.json['secret']:
            abort(403)

@app.route('/restful-redis/api/v1.0/publish', methods=['POST'])
def publish_message():
    if not request.json or not 'message' in request.json:
        abort(400)
    if len(request.json['message']) == 0:
        abort(400)

    if "CHANNEL" in os.environ:
        channel = os.environ['CHANNEL']
    else:
        channel = 'restful-redis'

    try:
        red = redis.StrictRedis("redis")
        subcount = red.publish(channel, request.json['message'])
    except:
        abort(500)

    response = {
      'status': "Success" if subcount > 0 else "Failure",
      'subscriber_count': subcount
    }
    return jsonify({'response': response}), 201


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

@app.errorhandler(403)
def unauthorised(error):
    return make_response(jsonify({'error': 'Unauthorized'}), 403)

@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)


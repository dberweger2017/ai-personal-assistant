from flask import Flask, request, jsonify
from tools.proton import get_emails_pure, send_email_pure, delete_email_pure

app = Flask(__name__)

@app.route('/', methods=['GET'])
def test():
    return jsonify({'message': 'Hello, World!'})

@app.route('/get_emails', methods=['GET'])
def get_emails():
    n = int(request.args.get('n', 3))
    search_keyword = request.args.get('search_keyword', None)
    only_unread = request.args.get('only_unread', 'false').lower() == 'true'

    result = get_emails_pure(n, search_keyword, only_unread)
    if 'error' in result:
        return jsonify(result), 500
    return jsonify(result)

@app.route('/send_email', methods=['POST'])
def send_email():
    try:
        recipients = request.json['recipients']
        subject = request.json['subject']
        html = request.json['html']
        send_email_pure(recipients, subject, html)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500    

@app.route('/delete_emails', methods=['POST'])
def delete_emails():
    try:
        email_ids = request.json['email_ids']
        delete_email_pure(email_ids)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
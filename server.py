from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import base64
import hashlib
from datetime import datetime
import os

import mysql.connector
from mysql.connector import Error
import base64
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins, change as needed


UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the folder if it doesn't exist
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Database configuration
db_config = {
    'user': 'flask',
    'password': 'mbass',
    'host': 'localhost',
    'database': 'flashfix_data'
}


def encrypt_password(text):
    first_split = text[0:len(text)//2]
    second_split = text[len(text)//2:]
    
    encoded_data_first_split = base64.b64encode(first_split.encode('utf-8'))
    encoded_data_second_split = hashlib.sha256(second_split.encode('utf-8'))
    hash_hex = encoded_data_second_split.hexdigest()
    encoded_str = encoded_data_first_split.decode('utf-8')
    get = f"{str(encoded_str)}.{str(hash_hex)}"
    return get
    
 

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    mdp = data.get('mdp')
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = "SELECT * FROM users WHERE phone_number = %s AND mdp = %s"
        cursor.execute(query,(phone,encrypt_password(mdp)))
        result = cursor.fetchone()
        if result:
            return jsonify("authenticated"),200
        else:
            return jsonify("unauthenticated"),400
    except Exception as e:
        print(e)
        return jsonify("error"), 500
    
@app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    phone = data.get('phone')
    mdp = data.get('mdp')   
    address = data.get('address')    
    nom = data.get('nom')
    prenom = data.get('prenom')   
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = "SELECT * from users WHERE phone_number = %s"
        cursor.execute(query,(phone,))
        result = cursor.fetchone()
        if result:
            return jsonify("already_registered") , 400
        else:
            try:
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()
                query = "INSERT INTO users(name, last_name,phone_number,mdp,address) VALUES(%s,%s,%s,%s,%s)"
                cursor.execute(query,(prenom,nom,phone,encrypt_password(mdp),address))
                connection.commit()
                return jsonify("success"), 200
            except Exception as e:
                
                print(e)
                return jsonify("Error"),500
    except Exception as e:
        print(e)
        return jsonify("Error"),500
    
          
@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    # Check if the file has a name
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save the file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    return jsonify({"message": "File uploaded successfully", "file_path": file_path}), 200          
@app.route('/updateService', methods=['POST'])
def updateService():
    data = request.json
    postId = data.get("postId")
    status = data.get("status")
    print(postId,status)
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = """
            UPDATE `services`
            SET status=%s
            WHERE id = %s;
        """
        cursor.execute(query,(status.strip(),int(postId),))
        connection.commit()
        return jsonify("done"), 200
    except Exception as e:
        print(e)
        return jsonify("error") , 400
    
    
@app.route('/getUsers', methods=['POST'])
def getUsers():
    data = request.json
    ph = data.get('type')
   
    if ph == 'all':
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT * FROM users"
            cursor.execute(query)
            result = cursor.fetchall()
            if result:
                result.pop('mdp',None)
                
            return jsonify(result), 200
        except Exception as e:
            return jsonify("error"),400
    else:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT  *  FROM users WHERE phone_number=%s "
            cursor.execute(query,(ph,))
            result = cursor.fetchone()
        
            if result:
                result.pop('mdp',None)
            return jsonify(result), 200
        except Exception as e:
            print(e)
            return jsonify("error"),400
@app.route('/createService', methods=['POST'])
def create_service():
    data = request.get_json()
    
    # Extract data from the request
    seller_id = data.get('seller_id')
    name = data.get('name')
    description = data.get('description')
    phone = data.get('phone')
    prix = data.get('prix')
    date_posted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
     
    # Validate inputs
    if not all([seller_id, name, description, phone, prix]):
        return jsonify({"message": "All fields are required"}), 400

    try:
        # Establish a database connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # SQL Query to insert the new service
        query = """
            INSERT INTO services (seller_id, name, description, date_posted, phone, prix)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (seller_id, name, description, date_posted, phone, prix))
        connection.commit()

        return jsonify({"message": "Service created successfully"}), 201
    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({"message": "Failed to create service"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()        
@app.route('/getServices', methods=['POST'])
def getServices():  
    data = request.json
    type = data.get('type')
    status = data.get('status')
    if type == "all":
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            query = "SELECT m.name AS sv_name ,m.prix as prix, m.id as ids ,s.name , s.last_name , m.description,m.date_posted,m.phone, m.status  FROM services m,users s WHERE s.phone_number=m.phone AND m.status=%s"
            cursor.execute(query,(status,))
            result = cursor.fetchall()
          
            return jsonify(result) , 200
        except Exception as e:
            print(e) 
            return jsonify('error') , 400
    else:
        try:
            type = type.replace('"','')
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            query = "SELECT m.name AS sv_name ,m.prix as prix, m.id as ids ,s.name , s.last_name , m.description,m.date_posted,m.phone, m.status FROM services m,users s WHERE m.phone=%s AND s.phone_number = %s"
            cursor.execute(query,(type,type))
            result = cursor.fetchall()
            return jsonify(result) , 200
        except Exception as e:
            print(e) 
            return jsonify('error') , 400
@app.route('/getMessages', methods=['POST'])
def getMessages():
    data = request.json
    sender = str(data.get("sender"))
    recev = str(data.get("receiver"))
    rec2 = str(data.get("rec2"))
    sen2 = str(data.get("sen2"))
    msg = data.get("msg")  
    ord_id = data.get("ord_id")
    order_name = data.get("order_name")
    
    type = data.get("type") 
    
    if type == 'get':
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT * FROM orders 
                WHERE (sender = %s AND receiver = %s AND service_id =%s) 
                OR (sender = %s AND receiver = %s AND service_id = %s)
            """
            cursor.execute(query, (sender, recev,ord_id, sen2, rec2,ord_id ))
    
            result = cursor.fetchall()
          
            return jsonify(result), 200
        except Exception as e:
            print(e)
            return jsonify("error"), 500
    elif type=="send":
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            query = "INSERT into orders(order_name,sender,receiver,message,service_id) VALUES(%s,%s,%s,%s,%s)"
            cursor.execute(query,(order_name,sender,recev,msg,ord_id))
            connection.commit()
            return jsonify("sent") , 200
        except Exception as e:
            print(e)
            return jsonify("error") , 500
    else:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
             
            query = """
                SELECT DISTINCT 
                    o.sender, 
                    sender_user.name AS sender_name, 
                    sender_user.last_name AS sender_last_name,
                    o.receiver, 
                    receiver_user.name AS receiver_name, 
                    receiver_user.last_name AS receiver_last_name,
                    o.order_name, 
                    s.prix, 
                    s.id AS service_id
                FROM orders o
                JOIN services s ON s.name = o.order_name
                JOIN users sender_user ON sender_user.phone_number = o.sender
                JOIN users receiver_user ON receiver_user.phone_number = o.receiver
                WHERE o.sender IN (%s, %s) OR o.receiver IN (%s,%s);
            """

            cursor.execute(query, (sender, recev,sender,recev))
 
            result = cursor.fetchall()
            print(result)
            for i in result:
                try:
                    conn = mysql.connector.connect(**db_config)
                    cur = conn.cursor(dictionary=True)
                    query_check_last_msg = "SELECT message FROM orders where (receiver = %s and sender = %s) OR (sender=%s and receiver=%s) ORDER BY delivery_date DESC LIMIT 1"
                    
                    cur.execute(query_check_last_msg,(i['receiver'],i['sender'],i['receiver'],i['sender']))
                    res = cur.fetchall()
                    
                    i['info'] = {"sen" : i['sender'], "rec" : i['receiver'], "last_msg" : res[0]['message']}
                     
                except Exception as e:
                    print(e)
                    return jsonify("error"), 500
           
            return jsonify(result) , 200
        except Exception as e:
            print(e)
            return jsonify("error") , 500   
        
        
if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")

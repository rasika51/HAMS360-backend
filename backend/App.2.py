from flask import Flask, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from mysql.connector.cursor import MySQLCursorDict as DictCursor
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow frontend to access the API

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'  # Change if using a different host
app.config['MYSQL_USER'] = 'root'  # Replace with your MySQL username
app.config['MYSQL_PASSWORD'] = ''  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'hospital_inventory'  # Replace with your database name

mysql = MySQL(app)

@app.route('/api/total-assets', methods=['GET'])
def get_total_assets():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM assets")  # Adjust the table name if needed
        total_assets = cur.fetchone()[0]
        cur.close()

        return jsonify({'totalAssets': total_assets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/total-resources', methods=['GET'])
def get_total_resources():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM resources")  # Adjust table name if different
        total_resources = cur.fetchone()[0]
        cur.close()
        return jsonify({'totalResources': total_resources})  # Return JSON response
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Return error response if any issue occurs

@app.route('/api/asset-timeline', methods=['GET'])
def get_asset_timeline():
    try:
        cursor = mysql.connection.cursor()
        query = """
            SELECT
                DATE_FORMAT(a.date, '%Y-%m-%d') AS date, 
                SUM(a.stock_count - a.deduction) AS total_assets
            FROM assets a
            GROUP BY DATE_FORMAT(a.date, '%Y-%m-%d')
            ORDER BY a.date ASC;
        """
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        # Convert query results into JSON format
        asset_data = [{'date': row[0], 'totalAssets': row[1]} for row in result]

        return jsonify({'chartData': asset_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/low-stock', methods=['GET'])
def get_low_stock():
    try:
        cursor = mysql.connection.cursor(DictCursor)
        
        # Modified query to work with your existing tables
        cursor.execute("""
            SELECT 
                a.id,
                r.name as resource_name,
                a.name as asset_name,
                a.stock_count,
                a.date as last_updated,
                r.section
            FROM assets a
            JOIN resources r ON a.resource_id = r.id
            WHERE a.stock_count < 10
            ORDER BY a.stock_count ASC
            LIMIT 5
        """)
        
        low_stock_items = cursor.fetchall()
        cursor.close()

        # Format the response
        formatted_items = [{
            'id': item['id'],
            'resourceName': item['resource_name'],
            'assetName': item['asset_name'],
            'stockCount': item['stock_count'],
            'lastUpdated': item['last_updated'].strftime('%Y-%m-%d'),
            'section': item['section']
        } for item in low_stock_items]
        
        return jsonify({'lowStockItems': formatted_items})

    except Exception as e:
        print(f"Error in low stock: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/recent-updates', methods=['GET'])
def get_recent_updates():
    try:
        # Create database cursor
        cursor = mysql.connection.cursor()
        
        # Execute SQL query to get recent updates
        query = """
            SELECT a.id, a.name AS asset_name, a.deduction, a.date, r.name AS resource_name 
            FROM assets a
            JOIN resources r ON a.resource_id = r.id
            ORDER BY a.date DESC
            LIMIT 10
        """
        cursor.execute(query)
        updates = cursor.fetchall()

        # Format the response data
        formatted_updates = []
        for update in updates:
            action = 'Increased' if update['deduction'] < 0 else 'Decreased'
            formatted_updates.append({
                'id': update['id'],
                'item': f"{update['resource_name']} ({update['asset_name']})",
                'action': action,
                'quantity': abs(update['deduction']),
                'date': update['date'].strftime('%Y-%m-%d')
            })

        return jsonify({
            'success': True,
            'recentUpdates': formatted_updates
        })

    except Exception as e:
        print(f"Error fetching recent updates: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch recent updates'
        }), 500

    finally:
        # Always close the cursor
        if 'cursor' in locals():
            cursor.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Run Flask on port 5001

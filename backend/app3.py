from flask import Flask, request, jsonify, send_file
from flask_mysqldb import MySQL
from flask_cors import CORS
import pandas as pd
from io import BytesIO
import pdfkit
import logging

app = Flask(__name__)
CORS(app)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hospital_inventory'

mysql = MySQL(app)

# Configure PDFKit
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
pdfkit_config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

logging.basicConfig(level=logging.DEBUG)

# Existing Report Endpoints
@app.route('/reports/types', methods=['GET'])
def get_resource_types():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT DISTINCT name FROM resources')
        data = cur.fetchall()
        resource_types = [{'type': row[0]} for row in data]
        cur.close()
        return jsonify(resource_types)
    except Exception as e:
        app.logger.error(f"Error fetching resource types: {str(e)}")
        return jsonify({'error': 'Failed to fetch resource types'}), 500

@app.route('/reports/download', methods=['GET'])
def download_asset_report():
    try:
        report_type = request.args.get('reportType')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        asset_name = request.args.get('assetName', None)

        if not report_type or not start_date or not end_date:
            return jsonify({'error': 'Missing parameters'}), 400

        cur = mysql.connection.cursor()
        query = '''
            SELECT a.name, a.stock_count, a.deduction, a.date, r.section 
            FROM assets a
            JOIN resources r ON a.resource_id = r.id
            WHERE r.name = %s AND a.date BETWEEN %s AND %s
        '''
        params = [report_type, start_date, end_date]

        if asset_name:
            query += ' AND a.name = %s'
            params.append(asset_name)

        cur.execute(query, params)
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()

        if not data:
            return jsonify({'error': 'No data found for the selected criteria'}), 404

        df = pd.DataFrame(data, columns=columns)
        html = df.to_html(index=False)
        pdf = pdfkit.from_string(html, False, configuration=pdfkit_config)

        return send_file(
            BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{report_type}_report_{start_date}_to_{end_date}.pdf'
        )

    except Exception as e:
        app.logger.error(f"Report generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@app.route('/reports/preview', methods=['GET'])
def preview_asset_report():
    try:
        report_type = request.args.get('reportType')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        asset_name = request.args.get('assetName', None)

        if not report_type or not start_date or not end_date:
            return jsonify({'error': 'Missing parameters'}), 400

        cur = mysql.connection.cursor()
        query = '''
            SELECT a.name, a.stock_count, a.deduction, a.date, r.section 
            FROM assets a
            JOIN resources r ON a.resource_id = r.id
            WHERE r.name = %s AND a.date BETWEEN %s AND %s
        '''
        params = [report_type, start_date, end_date]

        if asset_name:
            query += ' AND a.name = %s'
            params.append(asset_name)

        cur.execute(query, params)
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()

        report_data = [dict(zip(columns, row)) for row in data]
        return jsonify(report_data)

    except Exception as e:
        app.logger.error(f"Preview error: {str(e)}")
        return jsonify({'error': f'Failed to generate preview: {str(e)}'}), 500

# New Asset Search Endpoints
@app.route('/assets/search', methods=['GET'])
def search_asset():
    asset_name = request.args.get('assetName')
    if not asset_name:
        return jsonify({'error': 'Asset name is required'}), 400

    try:
        cur = mysql.connection.cursor()
        query = '''
            SELECT 
                a.name AS asset_name,
                r.name AS resource_name,
                a.stock_count,
                a.deduction,
                a.date,
                r.section
            FROM assets a
            JOIN resources r ON a.resource_id = r.id
            WHERE a.name = %s
        '''
        cur.execute(query, (asset_name,))
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()

        if not data:
            return jsonify({'error': 'No assets found with that name'}), 404

        results = [dict(zip(columns, row)) for row in data]
        return jsonify(results)

    except Exception as e:
        app.logger.error(f"Asset search error: {str(e)}")
        return jsonify({'error': f'Failed to search assets: {str(e)}'}), 500

@app.route('/assets/download', methods=['GET'])
def download_asset_search():
    asset_name = request.args.get('assetName')
    if not asset_name:
        return jsonify({'error': 'Asset name is required'}), 400

    try:
        cur = mysql.connection.cursor()
        query = '''
            SELECT 
                a.name AS asset_name,
                r.name AS resource_name,
                a.stock_count,
                a.deduction,
                a.date,
                r.section
            FROM assets a
            JOIN resources r ON a.resource_id = r.id
            WHERE a.name = %s
        '''
        cur.execute(query, (asset_name,))
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()

        if not data:
            return jsonify({'error': 'No assets found with that name'}), 404

        df = pd.DataFrame(data, columns=columns)
        html = df.to_html(index=False)
        pdf = pdfkit.from_string(html, False, configuration=pdfkit_config)

        return send_file(
            BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{asset_name}_report.pdf'
        )

    except Exception as e:
        app.logger.error(f"Asset download error: {str(e)}")
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)
    
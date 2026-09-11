from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
DB_CONF = "dbname=db_finishing_tracker user=postgres password=admin123 host=localhost port=5432"

URUTAN_FOLDER = [
    "dth", "label", "bonding", "rwb", "mobile operator", "cop", 
    "production", "rewinding", "autopacking", "manual packing", "fgh"
]

def dapatkan_skor_urut(file_path):
    if not file_path: return 999
    path_lower = file_path.lower()
    for indeks, nama_folder in enumerate(URUTAN_FOLDER):
        if nama_folder in path_lower: return indeks
    return 900

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cari', methods=['GET'])
def api_cari():
    query_lot = request.args.get('lot', '').strip()
    if not query_lot: return jsonify([])

    conn = psycopg2.connect(DB_CONF)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Ambil kolom keterangan_n dari database
    sql = """
        SELECT nama_file, nama_sheet, no_lot, file_path, keterangan_n,
               TO_CHAR(file_modified_at, 'DD-MM-YYYY HH24:MI') as tanggal_input
        FROM excel_tracker 
        WHERE no_lot = %s
    """
    cursor.execute(sql, (query_lot,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    filtered_results = []
    for row in results:
        nama_file_lower = row['nama_file'].lower()
        nama_sheet_lower = row['nama_sheet'].lower()
        if "mobile" in nama_file_lower and "overdue" in nama_sheet_lower: continue
        if "dth" in nama_file_lower and "wip" in nama_sheet_lower: continue
        filtered_results.append(row)
    
    results_sorted = sorted(filtered_results, key=lambda x: dapatkan_skor_urut(x['file_path']))
    return jsonify(results_sorted)

@app.route('/api/buka', methods=['POST'])
def api_buka():
    data = request.json or {}
    path_file = data.get('path', '')
    if path_file and os.path.exists(path_file):
        return send_file(path_file, as_attachment=True)
    return jsonify({"status": "error"}), 404

if __name__ == '__main__':
    # Membaca port otomatis dari server Koyeb, jika tidak ada gunakan default 8000
    port_koyeb = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port_koyeb)

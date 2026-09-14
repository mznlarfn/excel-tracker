from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '..', 'templates')

app = Flask(__name__, template_folder=template_dir)

# ----------------- KONFIGURASI UTAMA -----------------
# ⚠️ PENTING: Gunakan alamat Connection String Neon.tech Anda yang sudah aktif!
DB_CONF = "postgresql://neondb_owner:npg_zd6ZRfEQIBb8@ep-shy-term-b33g219e-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
# -----------------------------------------------------

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

# 📊 API STATISTIK: Diperbarui dengan konversi tipe data integer (CAST) agar hitungan bulan akurat 100%
@app.route('/api/statistik', methods=['GET'])
def api_statistik():
    try:
        # Mengubah input string ("09") menjadi integer murni (9) agar klop dengan database SQL
        bulan = int(request.args.get('bulan', datetime.now().month))
        tahun = int(request.args.get('tahun', datetime.now().year))
        
        conn = psycopg2.connect(DB_CONF)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Hitung total order lot unik yang dimodifikasi pada bulan & tahun terpilih
        query_order = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE CAST(EXTRACT(MONTH FROM file_modified_at) AS INTEGER) = %s 
              AND CAST(EXTRACT(YEAR FROM file_modified_at) AS INTEGER) = %s;
        """
        cursor.execute(query_order, (bulan, tahun))
        total_order = cursor.fetchone()['total']
        
        # 2. Hitung total lot krisis di FOLDER overdue (Akumulasi Realtime Global)
        cursor.execute("""
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE file_path ILIKE '%\\\\overdue\\\\%' OR file_path ILIKE '%/overdue/%';
        """)
        total_overdue = cursor.fetchone()['total']
        
        # 3. Hitung total lot yang sukses sampai ke FOLDER fgh pada bulan & tahun terpilih
        query_fgh = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE (file_path ILIKE '%\\\\fgh\\\\%' OR file_path ILIKE '%/fgh/%')
              AND CAST(EXTRACT(MONTH FROM file_modified_at) AS INTEGER) = %s 
              AND CAST(EXTRACT(YEAR FROM file_modified_at) AS INTEGER) = %s;
        """
        cursor.execute(query_fgh, (bulan, tahun))
        total_fgh = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "total_order": total_order,
            "total_overdue": total_overdue,
            "total_fgh": total_fgh
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cari', methods=['GET'])
def api_cari():
    query_lot = request.args.get('lot', '').strip()
    if not query_lot: return jsonify([])

    conn = psycopg2.connect(DB_CONF)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
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
        if "report mobile integrasi" in nama_file_lower and "overdue" in nama_sheet_lower: continue
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

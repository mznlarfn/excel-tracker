from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Menentukan jalur folder HTML secara absolut agar ramah terhadap sistem serverless Vercel
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '..', 'templates')

app = Flask(__name__, template_folder=template_dir)

# ----------------- KONFIGURASI UTAMA -----------------
# ⚠️ PENTING: Masukkan alamat Connection String Neon.tech Anda di sini!
DB_CONF = "postgresql://neondb_owner:npg_zd6ZRfEQIBb8@ep-shy-term-b33g219e-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
# -----------------------------------------------------

# 11 Urutan prioritas resmi folder pengerjaan Departemen Finishing
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
    
    # Ambil data dari database cloud Neon
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
        
        # 1. KUNCI UTAMA: Lewati jika nama file mengandung 'report mobile integrasi' DAN sheet mengandung 'overdue'
        if "report mobile integrasi" in nama_file_lower and "overdue" in nama_sheet_lower:
            continue
            
        # 2. Aturan keamanan tambahan untuk berkas mobile operator lainnya
        if "mobile" in nama_file_lower and "overdue" in nama_sheet_lower:
            continue
            
        # 3. Lewati jika file mengandung 'dth' DAN sheet mengandung 'wip'
        if "dth" in nama_file_lower and "wip" in nama_sheet_lower:
            continue
            
        filtered_results.append(row)
    
    # Urutkan hasil akhir murni berdasarkan prioritas daftar 11 folder di atas
    results_sorted = sorted(filtered_results, key=lambda x: dapatkan_skor_urut(x['file_path']))
    return jsonify(results_sorted)

@app.route('/api/buka', methods=['POST'])
def api_buka():
    data = request.json or {}
    path_file = data.get('path', '')
    if path_file and os.path.exists(path_file):
        return send_file(path_file, as_attachment=True)
    return jsonify({"status": "error"}), 404

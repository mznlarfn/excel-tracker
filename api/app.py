from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '..', 'templates')

app = Flask(__name__, template_folder=template_dir)

# ----------------- KONFIGURASI UTAMA -----------------
# ⚠️ PENTING: Gunakan alamat Connection String Neon.tech Anda yang sudah aktif!
DB_CONF = "from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '..', 'templates')

app = Flask(__name__, template_folder=template_dir)

# ----------------- KONFIGURASI UTAMA -----------------
# ⚠️ PENTING: Gunakan alamat Connection String Neon.tech Anda yang sudah aktif!
DB_CONF = "postgresql://postgres:password_kamu@ep-cool-pool-1234.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
# -----------------------------------------------------

URUTAN_FOLDER = [
    "dth", "label", "bonding", "rwb", "mobile operator", "cop", 
    "production", "rewinding", "autopacking", "manual packing", "fgh"
]

SINGKATAN_BULAN_KAPITAL = ["", "JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGU", "SEP", "OKT", "NOV", "DES"]

def dapatkan_skor_urut(file_path):
    if not file_path: return 999
    path_lower = file_path.lower()
    for indeks, nama_folder in enumerate(URUTAN_FOLDER):
        if nama_folder in path_lower: return indeks
    return 900

@app.route('/')
def index():
    return render_template('index.html')

# 📊 API STATISTIK: Diperbarui murni dinamis tanpa pengunci angka duplikat harian
@app.route('/api/statistik', methods=['GET'])
def api_statistik():
    try:
        angka_bulan = int(request.args.get('bulan', '9'))
        tahun = request.args.get('tahun', '2026')
        teks_bulan = SINGKATAN_BULAN_KAPITAL[angka_bulan]
        
        conn = psycopg2.connect(DB_CONF)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Pola saringan kata kunci teks penamaan dokumen pabrik Anda
        pola_bulan = f"%{teks_bulan}%"
        pola_tahun = f"%{tahun}%"
        
        # 1. TOTAL ORDER BULANAN MURNI DINAMIS
        query_order = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE file_path ILIKE %s AND file_path ILIKE %s;
        """
        cursor.execute(query_order, (pola_bulan, pola_tahun))
        total_order = cursor.fetchone()['total']
        if total_order is None: total_order = 0
        
        # 2. TOTAL OVERDUE GLOBAL REALTIME
        cursor.execute("""
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE file_path ILIKE '%\\\\overdue\\\\%' OR file_path ILIKE '%/overdue/%';
        """)
        total_overdue = cursor.fetchone()['total']
        if total_overdue is None: total_overdue = 0
        
        # 3. DESPATCH FGH BULANAN MURNI DINAMIS
        query_fgh = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE (file_path ILIKE '%\\\\fgh\\\\%' OR file_path ILIKE '%/fgh/%')
              AND file_path ILIKE %s 
              AND file_path ILIKE %s;
        """
        cursor.execute(query_fgh, (pola_bulan, pola_tahun))
        total_fgh = cursor.fetchone()['total']
        if total_fgh is None: total_fgh = 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "total_order": total_order,
            "total_overdue": total_overdue,
            "total_fgh": total_fgh
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/cari', methods=['GET'])
def api_cari():
    query_lot = request.args.get('lot', '').strip()
    if not query_lot: return jsonify([])

    try:
        conn = psycopg2.connect(DB_CONF)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT nama_file, nama_sheet, no_lot, file_path, keterangan_n,
                   COALESCE(TO_CHAR(file_modified_at, 'DD-MM-YYYY HH24:MI'), '12-09-2026 12:33') as tanggal_input
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
    except:
        return jsonify([])

@app.route('/api/buka', methods=['POST'])
def api_buka():
    data = request.json or {}
    path_file = data.get('path', '')
    if path_file and os.path.exists(path_file):
        return send_file(path_file, as_attachment=True)
    return jsonify({"status": "error"}), 404
"
# -----------------------------------------------------

URUTAN_FOLDER = [
    "dth", "label", "bonding", "rwb", "mobile operator", "cop", 
    "production", "rewinding", "autopacking", "manual packing", "fgh"
]

SINGKATAN_BULAN_KAPITAL = ["", "JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGU", "SEP", "OKT", "NOV", "DES"]

def dapatkan_skor_urut(file_path):
    if not file_path: return 999
    path_lower = file_path.lower()
    for indeks, nama_folder in enumerate(URUTAN_FOLDER):
        if nama_folder in path_lower: return indeks
    return 900

@app.route('/')
def index():
    return render_template('index.html')

# 📊 API STATISTIK: Diperbarui murni dinamis tanpa pengunci angka duplikat harian
@app.route('/api/statistik', methods=['GET'])
def api_statistik():
    try:
        angka_bulan = int(request.args.get('bulan', '9'))
        tahun = request.args.get('tahun', '2026')
        teks_bulan = SINGKATAN_BULAN_KAPITAL[angka_bulan]
        
        conn = psycopg2.connect(DB_CONF)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Pola saringan kata kunci teks penamaan dokumen pabrik Anda
        pola_bulan = f"%{teks_bulan}%"
        pola_tahun = f"%{tahun}%"
        
        # 1. TOTAL ORDER BULANAN MURNI DINAMIS
        query_order = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE file_path ILIKE %s AND file_path ILIKE %s;
        """
        cursor.execute(query_order, (pola_bulan, pola_tahun))
        total_order = cursor.fetchone()['total']
        if total_order is None: total_order = 0
        
        # 2. TOTAL OVERDUE GLOBAL REALTIME
        cursor.execute("""
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE file_path ILIKE '%\\\\overdue\\\\%' OR file_path ILIKE '%/overdue/%';
        """)
        total_overdue = cursor.fetchone()['total']
        if total_overdue is None: total_overdue = 0
        
        # 3. DESPATCH FGH BULANAN MURNI DINAMIS
        query_fgh = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE (file_path ILIKE '%\\\\fgh\\\\%' OR file_path ILIKE '%/fgh/%')
              AND file_path ILIKE %s 
              AND file_path ILIKE %s;
        """
        cursor.execute(query_fgh, (pola_bulan, pola_tahun))
        total_fgh = cursor.fetchone()['total']
        if total_fgh is None: total_fgh = 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "total_order": total_order,
            "total_overdue": total_overdue,
            "total_fgh": total_fgh
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/cari', methods=['GET'])
def api_cari():
    query_lot = request.args.get('lot', '').strip()
    if not query_lot: return jsonify([])

    try:
        conn = psycopg2.connect(DB_CONF)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT nama_file, nama_sheet, no_lot, file_path, keterangan_n,
                   COALESCE(TO_CHAR(file_modified_at, 'DD-MM-YYYY HH24:MI'), '12-09-2026 12:33') as tanggal_input
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
    except:
        return jsonify([])

@app.route('/api/buka', methods=['POST'])
def api_buka():
    data = request.json or {}
    path_file = data.get('path', '')
    if path_file and os.path.exists(path_file):
        return send_file(path_file, as_attachment=True)
    return jsonify({"status": "error"}), 404

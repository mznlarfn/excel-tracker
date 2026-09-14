from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os

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

# Kamus konversi angka bulan ke huruf BESAR murni sesuai format nama file Excel lantai pabrik Anda
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

# 📊 API STATISTIK: Diperbarui menggunakan fungsi UPPER agar filter bulan kebal dari error huruf besar/kecil
@app.route('/api/statistik', methods=['GET'])
def api_statistik():
    try:
        angka_bulan = int(request.args.get('bulan', '9'))
        tahun = request.args.get('tahun', '2026')
        
        teks_bulan_kapital = SINGKATAN_BULAN_KAPITAL[angka_bulan]
        
        conn = psycopg2.connect(DB_CONF)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 🔐 STRATEGI MUTLAK ANTI-GAGAL:
        # Menambahkan tanda % di sekeliling teks bulan dan tahun agar fleksibel membaca file (Misal: %SEP% dan %2026%)
        pola_filter_bulan = f"%{teks_bulan_kapital}%"
        pola_filter_tahun = f"%{tahun}%"
        
        # 1. TOTAL ORDER BULANAN (Kebal Huruf Besar / Kecil dengan fungsi UPPER)
        query_order = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE UPPER(file_path) LIKE %s AND UPPER(file_path) LIKE %s;
        """
        cursor.execute(query_order, (pola_filter_bulan, pola_filter_tahun))
        total_order = cursor.fetchone()['total']
        
        # Skenario Cadangan Aman: Jika user memilih bulan yang datanya memang belum di-index sama sekali, 
        # kembalikan nilai 0 asli agar visual grafik monitoring bulanan akurat.
        if total_order is None:
            total_order = 0
        
        # 2. TOTAL OVERDUE GLOBAL REALTIME
        cursor.execute("""
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE file_path ILIKE '%overdue%';
        """)
        total_overdue = cursor.fetchone()['total']
        
        # 3. DESPATCH FGH BULANAN (Kebal Huruf Besar / Kecil dengan fungsi UPPER)
        query_fgh = """
            SELECT COUNT(DISTINCT no_lot) as total 
            FROM excel_tracker 
            WHERE UPPER(file_path) LIKE '%FGH%' 
              AND UPPER(file_path) LIKE %s 
              AND UPPER(file_path) LIKE %s;
        """
        cursor.execute(query_fgh, (pola_filter_bulan, pola_filter_tahun))
        total_fgh = cursor.fetchone()['total']
        
        if total_fgh is None:
            total_fgh = 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "total_order": total_order,
            "total_overdue": total_overdue,
            "total_fgh": total_fgh
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/cari', methods=['GET'])
def api_cari():
    query_lot = request.args.get('lot', '').strip()
    if not query_lot: return jsonify([])

    conn = psycopg2.connect(DB_CONF)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    sql = """
        SELECT nama_file, nama_sheet, no_lot, file_path, keterangan_n,
               '12-09-2026 12:33' as tanggal_input
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

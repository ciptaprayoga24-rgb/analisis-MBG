from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_super_aman'  # Ganti dengan string acak bebas

# --- INITIALISASI DATABASE ---
def init_db():
    conn = sqlite3.connect('audit_bahan.db')
    cursor = conn.cursor()
    # Tabel User / Auditor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Tabel Bahan Baku
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bahan_baku (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_bahan TEXT NOT NULL,
            stok REAL NOT NULL,
            satuan TEXT NOT NULL,
            harga_satuan INTEGER NOT NULL
        )
    ''')
    
    # Buat akun auditor default jika belum ada (Username: auditor, Password: password123)
    cursor.execute("SELECT * FROM users WHERE username = 'auditor'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('password123')
        cursor.execute("INSERT INTO users (username, password) VALUES ('auditor', ?)", (hashed_pw,))
        
        # Contoh data bahan awal
        cursor.execute("INSERT INTO bahan_baku (nama_bahan, stok, satuan, harga_satuan) VALUES ('Tepung Terigu', 150.0, 'kg', 12000)")
        cursor.execute("INSERT INTO bahan_baku (nama_bahan, stok, satuan, harga_satuan) VALUES ('Gula Pasir', 80.0, 'kg', 16000)")
        
    conn.commit()
    conn.close()

# --- TEMPLATE HTML (Single File untuk Kemudahan) ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Sistem Audit Bahan Baku</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand mb-0 h1">Sistem Audit Bahan Baku</span>
            {% if session.get('logged_in') %}
                <span class="navbar-text">
                    Login sebagai: <strong>{{ session['username'] }}</strong> | 
                    <a href="{{ url_for('logout') }}" class="btn btn-sm btn-danger ms-2">Logout</a>
                </span>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('audit_bahan.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah!', 'error')
            
    return render_template_string(HTML_LAYOUT + """
    {% block content %}
    <div class="row justify-content-center">
        <div class="col-md-4 mt-5">
            <div class="card shadow">
                <div class="card-header bg-primary text-white text-center"><h4>Login Auditor</h4></div>
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" name="username" class="form-control" required autocomplete="off">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Masuk</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """)

@app.route('/')
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('audit_bahan.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bahan_baku")
    items = cursor.fetchall()
    conn.close()
    
    return render_template_string(HTML_LAYOUT + """
    {% block content %}
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2>Data Keseluruhan Bahan Baku</h2>
        <button class="btn btn-success" data-bs-toggle="collapse" data-bs-target="#formTambah">Tambah Bahan Baru</button>
    </div>
    
    <!-- Form Tambah Bahan -->
    <div class="collapse card mb-4 shadow-sm" id="formTambah">
        <div class="card-body">
            <h5>Tambah Data</h5>
            <form action="{{ url_for('tambah') }}" method="POST" class="row g-3">
                <div class="col-md-4"><input type="text" name="nama" class="form-control" placeholder="Nama Bahan" required></div>
                <div class="col-md-2"><input type="number" step="0.01" name="stok" class="form-control" placeholder="Stok" required></div>
                <div class="col-md-2"><input type="text" name="satuan" class="form-control" placeholder="Satuan (kg/liter/dll)" required></div>
                <div class="col-md-2"><input type="number" name="harga" class="form-control" placeholder="Harga Satuan" required></div>
                <div class="col-md-2"><button type="submit" class="btn btn-primary w-100">Simpan</button></div>
            </form>
        </div>
    </div>

    <!-- Tabel Data -->
    <div class="card shadow-sm">
        <div class="card-body">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Nama Bahan</th>
                        <th>Stok</th>
                        <th>Satuan</th>
                        <th>Harga Satuan</th>
                        <th class="text-center">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>{{ item[0] }}</td>
                        <td>{{ item[1] }}</td>
                        <td>{{ item[2] }}</td>
                        <td><span class="badge bg-secondary">{{ item[3] }}</span></td>
                        <td>Rp {{ "{:,.0f}".format(item[4]) }}</td>
                        <td class="text-center">
                            <a href="/edit/{{ item[0] }}" class="btn btn-warning btn-sm">Edit</a>
                            <a href="/hapus/{{ item[0] }}" class="btn btn-danger btn-sm" onclick="return confirm('Yakin ingin menghapus?')">Hapus</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% endblock %}
    """, items=items)

@app.route('/tambah', methods=['POST'])
def tambah():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    nama = request.form['nama']
    stok = request.form['stok']
    satuan = request.form['satuan']
    harga = request.form['harga']
    
    conn = sqlite3.connect('audit_bahan.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bahan_baku (nama_bahan, stok, satuan, harga_satuan) VALUES (?, ?, ?, ?)", (nama, stok, satuan, harga))
    conn.commit()
    conn.close()
    flash('Data berhasil ditambahkan!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = sqlite3.connect('audit_bahan.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nama = request.form['nama']
        stok = request.form['stok']
        satuan = request.form['satuan']
        harga = request.form['harga']
        
        cursor.execute("UPDATE bahan_baku SET nama_bahan=?, stok=?, satuan=?, harga_satuan=? WHERE id=?", (nama, stok, satuan, harga, id))
        conn.commit()
        conn.close()
        flash('Data berhasil diperbarui!', 'success')
        return redirect(url_for('dashboard'))
        
    cursor.execute("SELECT * FROM bahan_baku WHERE id=?", (id,))
    item = cursor.fetchone()
    conn.close()
    
    return render_template_string(HTML_LAYOUT + """
    {% block content %}
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow">
                <div class="card-header bg-warning"><h5>Edit Data Bahan Baku (ID: {{ item[0] }})</h5></div>
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3"><label class="form-label">Nama Bahan</label><input type="text" name="nama" value="{{ item[1] }}" class="form-control" required></div>
                        <div class="mb-3"><label class="form-label">Stok</label><input type="number" step="0.01" name="stok" value="{{ item[2] }}" class="form-control" required></div>
                        <div class="mb-3"><label class="form-label">Satuan</label><input type="text" name="satuan" value="{{ item[3] }}" class="form-control" required></div>
                        <div class="mb-3"><label class="form-label">Harga Satuan</label><input type="number" name="harga" value="{{ item[4] }}" class="form-control" required></div>
                        <button type="submit" class="btn btn-warning">Perbarui</button>
                        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Batal</a>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """, item=item)

@app.route('/hapus/<int:id>')
def hapus(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect('audit_bahan.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bahan_baku WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash('Data berhasil dihapus!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah keluar.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
import os
from flask import Flask, render_template_string, request, redirect, url_for
import pymysql

app = Flask(__name__)

VERSION = "1.0"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CIMB Demo App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f4f6f9; color: #333; }
        .header { background: #1a237e; color: white; padding: 20px 32px; display: flex; align-items: center; justify-content: space-between; }
        .header h1 { font-size: 20px; font-weight: 600; }
        .container { max-width: 860px; margin: 24px auto; padding: 0 16px; }

        /* Version Card - the star of the demo */
        .version-card {
            border-radius: 10px; padding: 28px 32px; margin-bottom: 24px;
            color: white; display: flex; align-items: center; gap: 32px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .version-number { font-size: 56px; font-weight: 800; line-height: 1; }
        .version-number span { font-size: 18px; font-weight: 400; display: block; opacity: 0.85; margin-bottom: 4px; letter-spacing: 1px; text-transform: uppercase; }
        .version-meta { font-size: 13px; line-height: 1.8; opacity: 0.9; }
        .version-meta strong { opacity: 1; }
        .version-divider { width: 2px; height: 72px; background: rgba(255,255,255,0.3); border-radius: 1px; }

        /* Standard cards */
        .card {
            background: white; border-radius: 8px; padding: 24px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .card h2 { font-size: 15px; color: #555; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #e8eaf6; text-align: left; padding: 10px 14px; font-size: 13px; color: #333; }
        td { padding: 10px 14px; border-bottom: 1px solid #eee; font-size: 14px; }
        .env-info { font-size: 13px; color: #777; }
        .env-info span { color: #1a237e; font-weight: 600; }
        .error { color: #c62828; background: #ffebee; padding: 16px; border-radius: 6px; font-size: 14px; }
        .success { color: #2e7d32; font-size: 13px; margin-bottom: 12px; }
        .footer { text-align: center; padding: 24px; font-size: 12px; color: #999; }
        .add-form { display: flex; gap: 10px; align-items: end; flex-wrap: wrap; }
        .add-form label { font-size: 12px; color: #555; display: block; margin-bottom: 4px; }
        .add-form input {
            padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px;
            font-size: 14px; outline: none;
        }
        .add-form input:focus { border-color: #1a237e; }
        .add-form button {
            background: #1a237e; color: white; border: none; padding: 9px 20px;
            border-radius: 4px; font-size: 14px; cursor: pointer;
        }
        .add-form button:hover { background: #283593; }
        .delete-btn {
            background: none; border: 1px solid #c62828; color: #c62828;
            padding: 3px 10px; border-radius: 3px; font-size: 12px; cursor: pointer;
        }
        .delete-btn:hover { background: #ffebee; }
        .flash { padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 13px; }
        .flash-success { background: #e8f5e9; color: #2e7d32; }
        .flash-error { background: #ffebee; color: #c62828; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Alibaba Cloud CI/CD Demo</h1>
        <div style="font-size: 13px; opacity: 0.8;">{{ hostname }}</div>
    </div>
    <div class="container">

        {% if flash_msg %}
        <div class="flash {{ flash_class }}">{{ flash_msg }}</div>
        {% endif %}

        <div class="version-card" style="background: {{ version_color }};">
            <div class="version-number">
                <span>Version</span>
                v{{ version }}
            </div>
            <div class="version-divider"></div>
            <div class="version-meta">
                <strong>Container:</strong> {{ hostname }}<br>
                <strong>Database:</strong> {{ db_name }}@{{ db_host_short }}<br>
                <strong>Environment:</strong> {{ app_env }}<br>
                <strong>Pipeline:</strong> GitHub &rarr; ACR &rarr; ECI / ACK / ACS
            </div>
        </div>

        {% if error %}
        <div class="card">
            <h2>Database Connection</h2>
            <p class="error">{{ error }}</p>
        </div>
        {% else %}

        <div class="card">
            <h2>Add a Product</h2>
            <form class="add-form" method="POST" action="/add">
                <div>
                    <label>Product Name</label>
                    <input type="text" name="name" placeholder="e.g. Alibaba Cloud SLB" required>
                </div>
                <div>
                    <label>Price (RM)</label>
                    <input type="number" name="price" step="0.01" min="0" placeholder="19.99" required>
                </div>
                <button type="submit">Add</button>
            </form>
        </div>

        <div class="card">
            <h2>Products from RDS MySQL</h2>
            <p class="success">Connected successfully — {{ products|length }} record(s) found</p>
            <table>
                <tr><th>ID</th><th>Product</th><th>Price</th><th>Created</th><th></th></tr>
                {% for p in products %}
                <tr>
                    <td>{{ p.id }}</td>
                    <td>{{ p.name }}</td>
                    <td>RM {{ "%.2f"|format(p.price) }}</td>
                    <td>{{ p.created_at }}</td>
                    <td>
                        <form method="POST" action="/delete/{{ p.id }}" style="display:inline">
                            <button type="submit" class="delete-btn">Delete</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
    </div>
    <div class="footer">Running on Alibaba Cloud ECI / ACK / ACS</div>
</body>
</html>
"""


def get_version_color(version_str):
    """Return a colour that changes per major version for visual CI/CD proof."""
    colors = {
        "1": "#1565c0",   # blue
        "2": "#2e7d32",   # green
        "3": "#e65100",   # orange
        "4": "#6a1b9a",   # purple
    }
    major = version_str.split(".")[0]
    return colors.get(major, "#455a64")


def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", ""),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", ""),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", ""),
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


def fetch_products():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, price, created_at FROM products ORDER BY id")
        products = cursor.fetchall()
    conn.close()
    return products


@app.route("/")
def index():
    db_host = os.environ.get("DB_HOST", "not set")
    db_name = os.environ.get("DB_NAME", "not set")
    db_user = os.environ.get("DB_USER", "not set")
    hostname = os.environ.get("HOSTNAME", "unknown")
    app_env = os.environ.get("APP_ENV", "demo")
    db_host_short = db_host.split(".")[0] if "." in db_host else db_host
    version_color = get_version_color(VERSION)

    try:
        products = fetch_products()
        return render_template_string(
            HTML_TEMPLATE,
            version=VERSION,
            version_color=version_color,
            products=products,
            db_host=db_host,
            db_host_short=db_host_short,
            db_name=db_name,
            db_user=db_user,
            hostname=hostname,
            app_env=app_env,
            error=None,
            flash_msg=request.args.get("msg"),
            flash_class="flash-success" if request.args.get("msg") else "",
        )
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            version=VERSION,
            version_color=version_color,
            products=[],
            db_host=db_host,
            db_host_short=db_host_short,
            db_name=db_name,
            db_user=db_user,
            hostname=hostname,
            app_env=app_env,
            error=str(e),
            flash_msg=None,
            flash_class="",
        )


@app.route("/add", methods=["POST"])
def add_product():
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "0").strip()

    if not name or not price:
        return redirect(url_for("index", msg="Name and price are required"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO products (name, price) VALUES (%s, %s)",
                (name, float(price)),
            )
        conn.commit()
        conn.close()
        return redirect(url_for("index", msg=f"Added: {name} (RM {float(price):.2f})"))
    except Exception as e:
        return redirect(url_for("index", msg=f"Error: {e}"))


@app.route("/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("index", msg=f"Deleted product ID {product_id}"))
    except Exception as e:
        return redirect(url_for("index", msg=f"Error: {e}"))


@app.route("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "version": VERSION}, 200
    except Exception:
        return {"status": "unhealthy", "version": VERSION}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

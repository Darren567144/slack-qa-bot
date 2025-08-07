"""
Add these routes to your start.py or create a separate web service
"""
from flask import Flask, jsonify, render_template_string
from database.database_manager import DatabaseManager

app = Flask(__name__)

@app.route('/data')
def show_data():
    """API endpoint to view Q&A data as JSON."""
    try:
        db = DatabaseManager()
        pairs = db.get_qa_pairs(limit=50)
        stats = db.get_statistics()
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'qa_pairs': pairs
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        })

@app.route('/web')
def web_dashboard():
    """Simple web dashboard to view data."""
    try:
        db = DatabaseManager()
        pairs = db.get_qa_pairs(limit=20)
        stats = db.get_statistics()
        
        html = """
        <h1>🤖 QA Bot Dashboard</h1>
        <div style="background: #f0f0f0; padding: 10px; margin: 10px 0;">
            <h3>📊 Statistics</h3>
            <p>Q&A Pairs: {{ stats.qa_pairs }}</p>
            <p>Questions: {{ stats.questions }}</p>
            <p>Processed Messages: {{ stats.processed_messages }}</p>
            <p>Database: {{ stats.database_path }}</p>
        </div>
        
        <h3>🔍 Recent Q&A Pairs</h3>
        {% for pair in pairs %}
        <div style="border: 1px solid #ddd; padding: 10px; margin: 5px 0;">
            <strong>Q:</strong> {{ pair.question }}<br>
            <strong>A:</strong> {{ pair.answer }}<br>
            <small>{{ pair.question_user }} → {{ pair.answer_user }} in {{ pair.channel }}</small>
        </div>
        {% endfor %}
        
        <p><a href="/data">View Raw JSON Data</a></p>
        """
        
        return render_template_string(html, pairs=pairs, stats=stats)
        
    except Exception as e:
        return f"Error: {e}"
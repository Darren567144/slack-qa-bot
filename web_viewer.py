#!/usr/bin/env python
"""
Optional web interface to view Q&A data stored in the database.
Run this separately or access via /web endpoint if integrated.
"""
import os
import sys
from pathlib import Path
from flask import Flask, render_template_string, jsonify, send_file
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.database_manager import DatabaseManager

app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Slack Q&A Bot Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5; color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #2c5aa0; }
        .stat-label { color: #666; margin-top: 5px; }
        .qa-pair { 
            background: white; margin: 20px 0; padding: 25px; border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 4px solid #4CAF50;
        }
        .question { 
            font-size: 1.1em; font-weight: 600; color: #2c5aa0; margin-bottom: 15px;
            padding: 15px; background: #f8f9ff; border-radius: 8px;
        }
        .answer { 
            color: #333; margin-bottom: 15px; padding: 15px; 
            background: #f9fff9; border-radius: 8px; line-height: 1.5;
        }
        .metadata { 
            display: flex; gap: 20px; flex-wrap: wrap; color: #666; font-size: 0.9em; 
            padding: 10px; background: #f8f8f8; border-radius: 6px;
        }
        .metadata span { padding: 5px 10px; background: white; border-radius: 4px; }
        .actions { margin: 30px 0; text-align: center; }
        .btn { 
            display: inline-block; padding: 12px 24px; margin: 0 10px; 
            background: #4CAF50; color: white; text-decoration: none; 
            border-radius: 6px; font-weight: 500; transition: background 0.3s;
        }
        .btn:hover { background: #45a049; }
        .btn-blue { background: #2196F3; }
        .btn-blue:hover { background: #1976D2; }
        .empty { text-align: center; color: #666; padding: 60px 20px; }
        h1 { color: #2c5aa0; margin: 0; }
        .subtitle { color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Slack Q&A Bot Dashboard</h1>
            <div class="subtitle">Real-time Q&A detection and storage system</div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{{ stats.qa_pairs or 0 }}</div>
                <div class="stat-label">Q&A Pairs</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ stats.questions or 0 }}</div>
                <div class="stat-label">Questions</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ stats.answers or 0 }}</div>
                <div class="stat-label">Answers</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ stats.unique_channels or 0 }}</div>
                <div class="stat-label">Channels</div>
            </div>
        </div>
        
        <div class="actions">
            <a href="/export" class="btn">📥 Download CSV</a>
            <a href="/api/qa" class="btn btn-blue">📄 View JSON</a>
            <a href="/" class="btn btn-blue">🔄 Refresh</a>
        </div>
        
        <h2>Recent Q&A Pairs</h2>
        
        {% if qa_pairs %}
            {% for pair in qa_pairs %}
            <div class="qa-pair">
                <div class="question">❓ {{ pair.question }}</div>
                <div class="answer">💡 {{ pair.answer }}</div>
                <div class="metadata">
                    <span>👤 {{ pair.question_user }} → {{ pair.answer_user }}</span>
                    <span>📍 #{{ pair.channel }}</span>
                    <span>⭐ {{ "%.1f"|format((pair.confidence_score or 0) * 100) }}% confidence</span>
                    {% if pair.timestamp %}
                    <span>🕒 {{ pair.timestamp.strftime('%Y-%m-%d %H:%M') if pair.timestamp.strftime else pair.timestamp[:16] }}</span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty">
                <h3>No Q&A pairs found yet</h3>
                <p>Start asking questions in your Slack channels!</p>
                <p>The bot will automatically detect and store Q&A pairs.</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard showing Q&A pairs and statistics."""
    try:
        db = DatabaseManager()
        qa_pairs = db.get_qa_pairs(limit=50)
        stats = db.get_statistics()
        return render_template_string(HTML_TEMPLATE, qa_pairs=qa_pairs, stats=stats)
    except Exception as e:
        return f"<h1>Database Error</h1><p>{str(e)}</p><p>Make sure the bot is running and database is accessible.</p>", 500

@app.route('/api/qa')
def api_qa():
    """JSON API endpoint for Q&A pairs."""
    try:
        db = DatabaseManager()
        qa_pairs = db.get_qa_pairs(limit=100)
        return jsonify({
            "status": "success",
            "count": len(qa_pairs),
            "qa_pairs": qa_pairs
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """JSON API endpoint for statistics."""
    try:
        db = DatabaseManager()
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/export')
def export_csv():
    """Export Q&A pairs as CSV file."""
    try:
        db = DatabaseManager()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        db.export_to_csv(tmp_path)
        return send_file(tmp_path, as_attachment=True, download_name='slack_qa_pairs.csv', mimetype='text/csv')
    
    except Exception as e:
        return f"<h1>Export Error</h1><p>{str(e)}</p>", 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        db = DatabaseManager()
        health = db.health_check()
        return jsonify(health)
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == '__main__':
    # For local testing
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
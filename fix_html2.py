with open("web/index.html", "r") as f:
    html = f.read()

# The cat command appended after </html>. We need to move it inside body.
# Let's remove it from the end and put it before script tags.

html = html.replace("""
  <!-- Interactive Server & Tool Parameter Inspector Modal -->
  <div id="inspectorModal" class="modal">
    <div class="modal-content" style="max-width: 900px; width: 95%;">
      <div class="modal-header">
        <div class="modal-title" id="inspectorTitle">Server Details</div>
        <button class="btn-close" onclick="closeInspectorModal()">&times;</button>
      </div>
      <div class="modal-body" id="inspectorBody" style="padding: 1.5rem;">
        <!-- Injected via JS -->
      </div>
    </div>
  </div>

  <style>
    #inspectorModal {
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.7);
      z-index: 200;
      align-items: center;
      justify-content: center;
    }
    #inspectorModal.show { display: flex; }
    
    .inspector-header-info {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }
    .inspector-header-info a {
      color: var(--accent);
      text-decoration: none;
    }
    .inspector-header-info a:hover {
      text-decoration: underline;
    }
    .inspector-meta-item {
      font-size: 0.9rem;
      color: var(--text-muted);
    }
    .inspector-meta-item strong {
      color: var(--text);
    }
    
    .tool-detail-card {
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      margin-bottom: 1rem;
    }
    .tool-detail-title {
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: var(--accent);
    }
    .tool-detail-desc {
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }
    
    .schema-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }
    .schema-table th, .schema-table td {
      border: 1px solid var(--border);
      padding: 0.5rem;
      text-align: left;
    }
    .schema-table th {
      background: #1e293b;
      color: var(--text);
      font-weight: 600;
    }
    .schema-table td {
      color: var(--text-muted);
    }
    .schema-table td.param-name {
      color: var(--text);
      font-weight: 500;
      font-family: monospace;
    }
    
    .copy-buttons-group {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-top: 1.5rem;
    }
  </style>""", "")

html = html.replace("</html>", "")

html = html.replace("""<script src="app.js"></script>
</body>""", """
  <!-- Interactive Server & Tool Parameter Inspector Modal -->
  <div id="inspectorModal" class="modal">
    <div class="modal-content" style="max-width: 900px; width: 95%;">
      <div class="modal-header">
        <div class="modal-title" id="inspectorTitle">Server Details</div>
        <button class="btn-close" onclick="closeInspectorModal()">&times;</button>
      </div>
      <div class="modal-body" id="inspectorBody" style="padding: 1.5rem;">
        <!-- Injected via JS -->
      </div>
    </div>
  </div>

  <style>
    #inspectorModal {
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.7);
      z-index: 200;
      align-items: center;
      justify-content: center;
    }
    #inspectorModal.show { display: flex; }
    
    .inspector-header-info {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }
    .inspector-header-info a {
      color: var(--accent);
      text-decoration: none;
    }
    .inspector-header-info a:hover {
      text-decoration: underline;
    }
    .inspector-meta-item {
      font-size: 0.9rem;
      color: var(--text-muted);
    }
    .inspector-meta-item strong {
      color: var(--text);
    }
    
    .tool-detail-card {
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      margin-bottom: 1rem;
    }
    .tool-detail-title {
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: var(--accent);
    }
    .tool-detail-desc {
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }
    
    .schema-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }
    .schema-table th, .schema-table td {
      border: 1px solid var(--border);
      padding: 0.5rem;
      text-align: left;
    }
    .schema-table th {
      background: #1e293b;
      color: var(--text);
      font-weight: 600;
    }
    .schema-table td {
      color: var(--text-muted);
    }
    .schema-table td.param-name {
      color: var(--text);
      font-weight: 500;
      font-family: monospace;
    }
    
    .copy-buttons-group {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-top: 1.5rem;
    }
  </style>

  <script src="app.js"></script>
</body>
</html>""")

with open("web/index.html", "w") as f:
    f.write(html)

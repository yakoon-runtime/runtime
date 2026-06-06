- su - pw mit Dialog -> Fokus form
- Jobs-flow verwendet derzeit die Platform
- api.* ist auch inden Plugins zu verwenden
- Projection asset -> Hier braucht es ein Dict, damit auch Bilder in der Projekte geladen werden können.

# TODOS:
1. y5nspace-ident → y5n.api (42 Dateien) – das große Migrationsthema für morgen
2. Web & SSH Apps reparieren (tote Imports, ~3 Minuten)
3. Zyklische Dependency lösen (session.py → PermissionSet)
4. Security-Lücken (SSH ohne Auth, Postgres Default Creds, SHA-256 ohne Salt)
5. Duplikat dsl copy/ löschen
7. **Collapsible paste in Projection** — Bei Pastes >5 Zeilen den Inhalt in der Projection als `collapsed=True` markieren, Client zeigt `[N lines inserted]` mit Expand per Enter/Tab/Klick. Nicht UI-Logik, sondern Projection-Protocol: Server steuert, Client rendert passend.

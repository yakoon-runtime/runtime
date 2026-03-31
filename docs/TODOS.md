kind: projection
state:
  role: info
  title: "Test – Inline Head"

  blocks:
    - type: list
      id: inline_list
      items:
        - 
          - type: code
            code: "cmd_a"
          - type: text
            text: " (controller_a)"
        - 
          - type: code
            code: "cmd_b"
          - type: text
            text: " (controller_b)"

            



## Neue Block-Typen implementieren

- type: spacer   -> Linie

list (strukturierte items, nicht string)
command_list (key + description)
  items:
    - key: "man"
      description: "Zeigt Manual für Befehle"
    - key: "use <prg>"
      description: "Startet ein Programm"
    - key: "version"
      description: "Zeigt Systeminformationen"

Tables rendern....
- type: table
  columns:
    - key
    - description
  rows: "{{ data.commands }}"

==================
# ✅ NEXT STEPS #
==================

steps:
  - id: customer_data
    input:
      fields:
        - { key: customer.first_name, label: "Vorname", required: true }
        - { key: customer.last_name,  label: "Nachname", required: true }
        - { key: customer.mail,       label: "E-Mail", required: false }
        - { key: customer.street,     label: "Straße", required: true }
        - { key: customer.zip,        label: "PLZ", required: true, validate: { regex: '^\d{5}$' } }
        - { key: customer.city,       label: "Ort", required: true }
        - { key: customer.phone,      label: "Telefon", required: false }
    actions:
      - { key: continue, label: "Weiter" }
      - { key: cancel,   label: "Abbruch" }
    next:
      continue: execute
      cancel: end_cancel

---

# Worklow Kunde

workflow: kunden_anlage
version: 1
roles: [sales, support]

steps:
  - id: first_name
    prompt:
      type: text
      title: "Vorname"
      var: customer.first_name
    next: last_name

  - id: last_name
    prompt:
      type: text
      title: "Nachname"
      var: customer.last_name
    next: ask_mail

  - id: ask_mail
    prompt:
      type: select
      title: "E-Mail angeben?"
      var: customer.mail_opt_in
      options:
        - {label: "Ja", value: yes}
        - {label: "Nein", value: no}
    branch:
      yes: mail
      no: street

  - id: mail
    prompt:
      type: text
      title: "E-Mail"
      var: customer.mail
    next: street

  - id: street
    prompt:
      type: text
      title: "Straße"
      var: customer.street
    next: zip

  - id: zip
    prompt:
      type: text
      title: "PLZ"
      var: customer.zip
    next: zip_validate

  - id: zip_validate
    validate:
      rule: regex
      var: customer.zip
      pattern: '^\d{5}$'
      error: "Bitte 5-stellige PLZ eingeben."
    branch:
      ok: city
      fail: zip

  - id: city
    prompt:
      type: text
      title: "Ort"
      var: customer.city
    next: phone

  - id: phone
    prompt:
      type: text
      title: "Telefon"
      var: customer.phone
    next: confirm

  - id: confirm
    prompt:
      type: review
      title: "Weiter oder Abbruch?"
      require_ack: true
      actions:
        - {label: "Weiter", value: continue}
        - {label: "Abbruch", value: cancel}
    branch:
      continue: execute
      cancel: end_cancel

  - id: execute
    run: "crm.create_customer {{customer}}"
    audit: true
    next: end_ok

  - id: end_ok
    end: ok

  - id: end_cancel
    end: cancel

---

workflow: deploy_service
version: 1
roles: [devops, sre]
steps:
  - id: pick_target                     ==> Wäre dann ein command im System
    ui:
      type: select                      ==> Prompt
      title: "Zielsystem"               ==> Titel im Promtp
      source: "discovery.targets"       ==> Interne Information für das Command 
  - id: confirm                         ==> Nächstes Command
    ui:
      type: review
      require_ack: true
  - id: execute
    run: "deploy --target {{pick_target.value}}"
    audit: true
    approvals:
      required: 1
      from_roles: [sre]

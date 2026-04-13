kind: ui_contract
id: crm.person
mode: replace   # replace | append (für den ganzen Contract)

projection:
  kind: message
  role: info
  title: "Person anlegen"
  blocks:
    - type: text
      text: "Legen Sie eine Person an ..."

input:
  kind: form
  form_id: crm.person
  fields:
    customer.first_name: { policy: system:string, title: "Vorname", required: true }
    customer.last_name:  { policy: system:string, title: "Nachname",  required: true }


Workflow
- id: person
  input:
    ui_ref: crm.person
    fields:
      - { id: customer.first_name, name: customer.first_name }
      - { id: customer.last_name,  name: customer.last_name }
  next: ask_mail

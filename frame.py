# frame.py
import pandas as pd

# ──────────────────────────────────────────────────────────────
# 1) Полное описание столбцов и ограничений каждой таблицы
# ──────────────────────────────────────────────────────────────
schema_data = [
    # ── location ─────────────────────────────────────────────
    {"table": "location", "column": "id",              "type": "serial",        "constraints": "PRIMARY KEY"},
    {"table": "location", "column": "location_name",   "type": "varchar(255)",  "constraints": "UNIQUE NOT NULL"},
    {"table": "location", "column": "description",     "type": "text",          "constraints": "NULL"},
    # ── device ───────────────────────────────────────────────
    {"table": "device", "column": "id",                "type": "serial",        "constraints": "PRIMARY KEY"},
    {"table": "device", "column": "location_id",       "type": "integer",       "constraints": "FK &rarr; location(id) ON CASCADE"},
    {"table": "device", "column": "inventory_number",  "type": "varchar(50)",   "constraints": "UNIQUE NOT NULL"},
    {"table": "device", "column": "type",              "type": "varchar(50)",   "constraints": "NULL"},
    {"table": "device", "column": "date_of_installation","type":"date",         "constraints": "NULL"},
    {"table": "device", "column": "latitude",          "type": "decimal(10,6)", "constraints": "NULL"},
    {"table": "device", "column": "longitude",         "type": "decimal(10,6)", "constraints": "NULL"},
    # ── environmental_parameters ─────────────────────────────
    {"table": "environmental_parameters", "column": "id",           "type": "serial",        "constraints": "PRIMARY KEY"},
    {"table": "environmental_parameters", "column": "device_id",    "type": "integer",       "constraints": "FK &rarr; device(id) ON CASCADE"},
    {"table": "environmental_parameters", "column": "temperature",  "type": "decimal(5,2)",  "constraints": "CHECK -50 &le; t° &le; 200"},
    {"table": "environmental_parameters", "column": "humidity",     "type": "decimal(5,2)",  "constraints": "CHECK 0 &le; h &le; 100"},
    {"table": "environmental_parameters", "column": "co2_level",    "type": "decimal(10,2)", "constraints": "CHECK &ge; 0"},
    {"table": "environmental_parameters", "column": "recorded_at",  "type": "timestamptz",   "constraints": "DEFAULT now()"},
    {"table": "environmental_parameters", "column": "processed",    "type": "boolean",       "constraints": "DEFAULT false"},
    # ── analyzed_information ─────────────────────────────────
    {"table": "analyzed_information", "column": "id",             "type": "serial",        "constraints": "PRIMARY KEY"},
    {"table": "analyzed_information", "column": "recorded_data_id","type": "integer",       "constraints": "FK &rarr; environmental_parameters(id) ON CASCADE"},
    {"table": "analyzed_information", "column": "fire_hazard",    "type": "decimal(5,2)",  "constraints": "NULL"},
    {"table": "analyzed_information", "column": "analyzed_at",    "type": "timestamptz",   "constraints": "DEFAULT now()"},
    # ── alarm ────────────────────────────────────────────────
    {"table": "alarm", "column": "id",               "type": "serial",        "constraints": "PRIMARY KEY"},
    {"table": "alarm", "column": "analysis_id",      "type": "integer",       "constraints": "FK &rarr; analyzed_information(id) ON PROTECT"},
    {"table": "alarm", "column": "incident_id",      "type": "integer",       "constraints": "FK &rarr; incident(id) ON SET NULL"},
    {"table": "alarm", "column": "status",           "type": "varchar(20)",   "constraints": "DEFAULT 'active'"},
    {"table": "alarm", "column": "alarm_level",      "type": "varchar(20)",   "constraints": "NOT NULL"},
    {"table": "alarm", "column": "alarm_at",         "type": "timestamptz",   "constraints": "NOT NULL"},
    # ── incident ─────────────────────────────────────────────
    {"table": "incident", "column": "id",                "type": "serial",        "constraints": "PRIMARY KEY"},
    {"table": "incident", "column": "location_id",       "type": "integer",       "constraints": "FK &rarr; location(id) ON PROTECT NULLABLE"},
    {"table": "incident", "column": "time_window_start", "type": "timestamptz",   "constraints": "DEFAULT now()"},
    {"table": "incident", "column": "time_window_end",   "type": "timestamptz",   "constraints": "NULL"},
    {"table": "incident", "column": "detected_at",       "type": "timestamptz",   "constraints": "DEFAULT now()"},
    {"table": "incident", "column": "description",       "type": "text",          "constraints": "NULL"},
    {"table": "incident", "column": "resolved_at",       "type": "timestamptz",   "constraints": "NULL"},
    {"table": "incident", "column": "status",            "type": "varchar(20)",   "constraints": "DEFAULT 'open'"},
    # ── incident_status_history ─────────────────────────────
    {"table": "incident_status_history", "column": "id",          "type": "serial",        "constraints": "PRIMARY KEY"},
    {"table": "incident_status_history", "column": "incident_id", "type": "integer",       "constraints": "FK &rarr; incident(id) ON CASCADE"},
    {"table": "incident_status_history", "column": "old_status",  "type": "varchar(20)",   "constraints": "NULL"},
    {"table": "incident_status_history", "column": "new_status",  "type": "varchar(20)",   "constraints": "NOT NULL"},
    {"table": "incident_status_history", "column": "changed_at",  "type": "timestamptz",   "constraints": "DEFAULT now()"},
    {"table": "incident_status_history", "column": "changed_by_id","type": "integer",      "constraints": "FK &rarr; auth_user(id) ON SET NULL"},
    {"table": "incident_status_history", "column": "comment",     "type": "text",          "constraints": "NULL"},
]

schema_df = pd.DataFrame(schema_data)

# ──────────────────────────────────────────────────────────────
# 2) Внешние ключи и их семантика
# ──────────────────────────────────────────────────────────────
relations_data = [
    {"from_table": "device",                    "from_column": "location_id",       "to_table": "location",                "to_column": "id",           "on_delete": "CASCADE",  "cardinality": "many-to-one"},
    {"from_table": "environmental_parameters",  "from_column": "device_id",         "to_table": "device",                  "to_column": "id",           "on_delete": "CASCADE",  "cardinality": "many-to-one"},
    {"from_table": "analyzed_information",      "from_column": "recorded_data_id",  "to_table": "environmental_parameters","to_column": "id",           "on_delete": "CASCADE",  "cardinality": "one-to-one"},
    {"from_table": "alarm",                     "from_column": "analysis_id",       "to_table": "analyzed_information",    "to_column": "id",           "on_delete": "PROTECT",  "cardinality": "many-to-one"},
    {"from_table": "alarm",                     "from_column": "incident_id",       "to_table": "incident",                "to_column": "id",           "on_delete": "SET NULL", "cardinality": "many-to-one"},
    {"from_table": "incident",                  "from_column": "location_id",       "to_table": "location",                "to_column": "id",           "on_delete": "PROTECT",  "cardinality": "many-to-one"},
    {"from_table": "incident_status_history",   "from_column": "incident_id",       "to_table": "incident",                "to_column": "id",           "on_delete": "CASCADE",  "cardinality": "many-to-one"},
    {"from_table": "incident_status_history",   "from_column": "changed_by_id",     "to_table": "auth_user",               "to_column": "id",           "on_delete": "SET NULL", "cardinality": "many-to-one"},
]

relations_df = pd.DataFrame(relations_data)

# ──────────────────────────────────────────────────────────────
# печатаем
# ──────────────────────────────────────────────────────────────
pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

print("=== Database Schema ===")
print(schema_df.to_string(index=False))

print("\n=== Entity Relationships ===")
print(relations_df.to_string(index=False))
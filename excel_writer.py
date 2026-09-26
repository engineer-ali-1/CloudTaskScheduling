
import pandas as pd
import os

def save_to_excel(mapping, file_path="output/task_vm_mapping.xlsx", metrics=None, vm_rows=None):
    df = pd.DataFrame(mapping)
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Task Mapping", index=False)
        if vm_rows is not None:
            pd.DataFrame(vm_rows).to_excel(writer, sheet_name="VM Summary", index=False)
        if metrics is not None:
            pd.DataFrame([metrics]).to_excel(writer, sheet_name="Run Metrics", index=False)
    return file_path

import os

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

def get_final_priority_score(district: str, base_severity: int) -> float:
    """
    Queries BigQuery for demographic and infrastructure data for the district.
    Calculates a final priority score by combining the AI's base severity
    with the district's vulnerability index.
    """
    if MOCK_MODE:
        print(f"[MOCK] Simulating BigQuery lookup for district: {district}")
        # In mock mode, we just add a random bump based on length of district name
        vulnerability_modifier = (len(district) % 5) / 2.0 
        final_score = min(10.0, base_severity + vulnerability_modifier)
        return round(final_score, 1)

    from google.cloud import bigquery
    client = bigquery.Client()
    
    # Example dataset: jandhwani_data.district_demographics
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID", "jandhwani_data")
    table_id = os.getenv("BQ_TABLE_ID", "district_demographics")
    
    # Sanitize inputs in production!
    query = f"""
        SELECT poverty_index, infra_access_score 
        FROM `{project_id}.{dataset_id}.{table_id}` 
        WHERE district_name = @district
        LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("district", "STRING", district)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = list(query_job.result())
    
    if not results:
        # District not found, return base severity
        return float(base_severity)
        
    row = results[0]
    poverty_index = row.poverty_index # 0.0 to 1.0 (higher means poorer)
    infra_access_score = row.infra_access_score # 0.0 to 1.0 (higher means better access)
    
    # Formula: 
    # Base Severity (1-10) 
    # + Poverty Bonus (up to +2.0) 
    # - Infra Access Penalty (up to -1.0)
    
    poverty_bonus = poverty_index * 2.0
    infra_penalty = infra_access_score * 1.0
    
    final_score = base_severity + poverty_bonus - infra_penalty
    
    # Clamp between 1.0 and 10.0
    final_score = max(1.0, min(10.0, final_score))
    
    return round(final_score, 1)

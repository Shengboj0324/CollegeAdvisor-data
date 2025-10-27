#!/usr/bin/env python3
"""
Ingest All Training Data into ChromaDB
Comprehensive ingestion of all JSONL files into appropriate collections
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_existing_database(db_path: str):
    """Clear existing ChromaDB database"""
    db_path_obj = Path(db_path)
    if db_path_obj.exists():
        logger.info(f"Removing existing database at {db_path}")
        shutil.rmtree(db_path)
    db_path_obj.mkdir(parents=True, exist_ok=True)


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load records from JSONL file"""
    records = []
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return records
        
    with open(file_path, 'r') as f:
        for line in f:
            try:
                records.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing line in {file_path}: {e}")
                
    return records


def create_document_text(record: Dict, record_type: str) -> str:
    """Create searchable text from record"""
    
    if record_type == "aid_policy":
        school = record.get("school_name", "")
        topic = record.get("policy_topic", "")
        rule = record.get("rule", "")
        return f"{school} | {topic} | {rule}"
        
    elif record_type == "international_aid":
        school = record.get("school_name", "")
        need_blind = "need-blind" if record.get("need_blind_international") else "need-aware"
        meets_need = "meets full need" if record.get("meets_full_need_international") else "limited aid"
        merit = "merit available" if record.get("merit_available_international") else "no merit"
        return f"{school} | International students | {need_blind} | {meets_need} | {merit}"
        
    elif record_type == "major_gate":
        school = record.get("school_name", "")
        major = record.get("major_name", "")
        gate_type = record.get("gate_type", "")
        rule = record.get("rule", "")
        return f"{school} | {major} | {gate_type} | {rule}"
        
    elif record_type == "residency":
        system = record.get("system", record.get("school_name", ""))
        rule_type = record.get("rule_type", "")
        requirement = record.get("requirement", "")
        details = record.get("details", "")
        return f"{system} | {rule_type} | {requirement} | {details}"
        
    elif record_type == "bsmd":
        program = record.get("program_name", "")
        undergrad = record.get("undergrad_school", "")
        med_school = record.get("medical_school", "")
        details = record.get("conditional_guarantee", "")
        return f"{program} | {undergrad} | {med_school} | {details}"
        
    elif record_type == "visa":
        rule_type = record.get("rule_type", "")
        requirement = record.get("requirement", "")
        details = record.get("details", "")
        return f"{rule_type} | {requirement} | {details}"
        
    elif record_type == "sai_example":
        scenario = record.get("scenario_name", "")
        sai = record.get("sai_result", {}).get("sai", 0)
        return f"SAI Example | {scenario} | SAI: {sai}"
        
    elif record_type == "npc":
        school = record.get("school_name", "")
        income = record.get("family_income", 0)
        efc = record.get("expected_family_contribution", 0)
        return f"{school} | Income: ${income} | EFC: ${efc}"
        
    elif record_type == "articulation":
        from_school = record.get("from_institution", "")
        to_school = record.get("to_institution", "")
        from_course = record.get("from_course_id", "")
        to_course = record.get("to_course_id", "")
        return f"{from_school} {from_course} → {to_school} {to_course}"
        
    elif record_type == "cds":
        school = record.get("school_name", "")
        section = record.get("section", "")
        return f"{school} | CDS {section}"
        
    elif record_type == "admit_rate":
        school = record.get("school_name", "")
        major = record.get("major", "")
        rate = record.get("major_admit_rate", 0)
        return f"{school} | {major} | Admit rate: {rate*100:.1f}%"
        
    elif record_type == "cited_answer":
        question = record.get("question", "")
        return f"Q: {question}"
        
    else:
        return json.dumps(record)


def ingest_collection(client: chromadb.Client, collection_name: str, records: List[Dict], record_type: str):
    """Ingest records into a collection"""
    if not records:
        logger.warning(f"No records to ingest for {collection_name}")
        return
        
    logger.info(f"Ingesting {len(records)} records into {collection_name}...")
    
    # Create or get collection
    try:
        client.delete_collection(collection_name)
    except:
        pass
    collection = client.create_collection(collection_name)
    
    # Prepare data for ingestion
    documents = []
    metadatas = []
    ids = []
    
    for i, record in enumerate(records):
        # Create document text
        doc_text = create_document_text(record, record_type)
        documents.append(doc_text)
        
        # Create metadata (flatten nested structures)
        metadata = {}
        for key, value in record.items():
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
            elif isinstance(value, list):
                metadata[key] = json.dumps(value)
            elif isinstance(value, dict):
                metadata[key] = json.dumps(value)
            else:
                metadata[key] = str(value)
        metadatas.append(metadata)
        
        # Create ID
        ids.append(f"{collection_name}_{i}")
    
    # Ingest in batches
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
    
    logger.info(f"✓ Ingested {len(records)} records into {collection_name}")


def main():
    """Main ingestion pipeline"""
    logger.info("="*80)
    logger.info("INGESTING ALL TRAINING DATA INTO CHROMADB")
    logger.info("="*80)
    
    # Clear existing database
    db_path = "./chroma_data"
    clear_existing_database(db_path)
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Define data sources and their collection mappings
    data_sources = [
        # Aid policies collection
        {
            "files": [
                "training_data/tier0_policy_rules/InstitutionAidPolicy.jsonl",
                "training_data/tier0_policy_rules/InternationalAidPolicy.jsonl",
            ],
            "collection": "aid_policies",
            "record_types": ["aid_policy", "international_aid"]
        },
        # Major gates collection
        {
            "files": [
                "training_data/tier0_policy_rules/MajorGate.jsonl",
                "training_data/tier0_policy_rules/ResidencyRule.jsonl",
                "training_data/tier0_policy_rules/BSMDProgram.jsonl",
                "training_data/tier0_policy_rules/VisaImmigration.jsonl",
                "training_data/tier1_admissions/AdmitRateByMajor.jsonl",
                "training_data/tier0_policy_rules/MilitaryDependentResidency.jsonl",
                "training_data/tier0_policy_rules/TribalCollegePolicy.jsonl",
                "training_data/tier0_policy_rules/UndocumentedDACAPolicy.jsonl",
                "training_data/tier0_policy_rules/FosterCarePolicy.jsonl",
                "training_data/tier0_policy_rules/DisabilityAccommodations.jsonl",
            ],
            "collection": "major_gates",
            "record_types": ["major_gate", "residency", "bsmd", "visa", "admit_rate", "military", "tribal", "daca", "foster", "disability"]
        },
        # CDS data collection
        {
            "files": [
                "training_data/tier1_admissions/CDSExtract.jsonl",
            ],
            "collection": "cds_data",
            "record_types": ["cds"]
        },
        # Articulation collection
        {
            "files": [
                "training_data/tier1_transfer/Articulation.jsonl",
            ],
            "collection": "articulation",
            "record_types": ["articulation"]
        },
        # Cited answers collection
        {
            "files": [
                "training_data/tier0_citation_training/CitedAnswer.jsonl",
                "training_data/tier0_policy_rules/SAIExample.jsonl",
                "training_data/tier1_costs/NPCResult.jsonl",
            ],
            "collection": "cited_answers",
            "record_types": ["cited_answer", "sai_example", "npc"]
        },
    ]
    
    # Ingest each collection
    total_records = 0
    for source in data_sources:
        all_records = []
        for file_path, record_type in zip(source["files"], source["record_types"]):
            records = load_jsonl(Path(file_path))
            if records:
                # Tag records with type for document creation
                for record in records:
                    record["_record_type"] = record_type
                all_records.extend(records)
                logger.info(f"  Loaded {len(records)} records from {Path(file_path).name}")
        
        if all_records:
            # Use first record type for collection (they're all going to same collection)
            ingest_collection(client, source["collection"], all_records, source["record_types"][0])
            total_records += len(all_records)
    
    logger.info("\n" + "="*80)
    logger.info(f"INGESTION COMPLETE: {total_records} total records")
    logger.info("="*80)
    
    # Verify collections
    logger.info("\nVerifying collections:")
    for collection_name in ["aid_policies", "major_gates", "cds_data", "articulation", "cited_answers"]:
        try:
            collection = client.get_collection(collection_name)
            count = collection.count()
            logger.info(f"  ✓ {collection_name}: {count} documents")
        except Exception as e:
            logger.error(f"  ✗ {collection_name}: {e}")


if __name__ == "__main__":
    main()


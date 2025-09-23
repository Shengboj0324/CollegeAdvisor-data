#!/usr/bin/env python3
"""
Create sample college data for testing the RAG system.
"""

import json
from pathlib import Path
from datetime import datetime

def create_sample_colleges():
    """Create sample college data following the schema."""
    
    colleges = [
        {
            "id": "stanford_cs",
            "name": "Stanford University",
            "type": "university",
            "location": "California, USA",
            "description": "Stanford University offers one of the top computer science programs in the world. The program covers artificial intelligence, machine learning, systems, theory, and human-computer interaction. Students have access to cutting-edge research facilities and work with renowned faculty. The program requires strong mathematical background and programming skills. Admission is highly competitive with average GPA of 3.9+.",
            "programs": ["Computer Science", "Artificial Intelligence", "Machine Learning", "Software Engineering"],
            "gpa_requirement": "3.9",
            "tuition": 56169,
            "acceptance_rate": 0.04,
            "ranking": 1,
            "website": "https://cs.stanford.edu",
            "year": 2024
        },
        {
            "id": "mit_cs",
            "name": "Massachusetts Institute of Technology",
            "type": "university", 
            "location": "Massachusetts, USA",
            "description": "MIT's Computer Science and Artificial Intelligence Laboratory (CSAIL) is the largest research laboratory at MIT. The program emphasizes both theoretical foundations and practical applications. Students can specialize in areas like robotics, computer graphics, programming languages, and distributed systems. The curriculum includes rigorous mathematics and hands-on projects. Strong preparation in calculus and physics is recommended.",
            "programs": ["Computer Science", "Electrical Engineering", "Robotics", "AI Research"],
            "gpa_requirement": "3.8",
            "tuition": 57986,
            "acceptance_rate": 0.07,
            "ranking": 2,
            "website": "https://www.csail.mit.edu",
            "year": 2024
        },
        {
            "id": "berkeley_cs",
            "name": "University of California, Berkeley",
            "type": "university",
            "location": "California, USA", 
            "description": "UC Berkeley's computer science program is known for its excellence in both research and education. The program offers strong foundations in algorithms, data structures, computer systems, and software engineering. Students can choose from tracks in artificial intelligence, graphics, human-computer interaction, programming languages, security, systems, and theory. The program has produced many successful entrepreneurs and researchers.",
            "programs": ["Computer Science", "Data Science", "Electrical Engineering", "Information Systems"],
            "gpa_requirement": "3.7",
            "tuition": 14254,
            "acceptance_rate": 0.17,
            "ranking": 3,
            "website": "https://eecs.berkeley.edu",
            "year": 2024
        },
        {
            "id": "cmu_cs",
            "name": "Carnegie Mellon University",
            "type": "university",
            "location": "Pennsylvania, USA",
            "description": "Carnegie Mellon's School of Computer Science is renowned for its rigorous curriculum and innovative research. The program covers computer systems, artificial intelligence, machine learning, robotics, and software engineering. Students work on real-world projects and have access to state-of-the-art facilities. The program emphasizes both theoretical knowledge and practical skills. Strong mathematical background is essential.",
            "programs": ["Computer Science", "Software Engineering", "Machine Learning", "Robotics"],
            "gpa_requirement": "3.8",
            "tuition": 59864,
            "acceptance_rate": 0.15,
            "ranking": 4,
            "website": "https://www.cs.cmu.edu",
            "year": 2024
        },
        {
            "id": "caltech_cs",
            "name": "California Institute of Technology",
            "type": "university",
            "location": "California, USA",
            "description": "Caltech's computer science program emphasizes the mathematical and scientific foundations of computing. The small program size allows for close interaction with faculty and personalized attention. Students study algorithms, computer systems, machine learning, and computational biology. The program is highly research-focused with opportunities to work on cutting-edge projects. Strong background in mathematics and physics is required.",
            "programs": ["Computer Science", "Applied Mathematics", "Computational Biology", "Machine Learning"],
            "gpa_requirement": "3.9",
            "tuition": 58680,
            "acceptance_rate": 0.06,
            "ranking": 5,
            "website": "https://www.cms.caltech.edu",
            "year": 2024
        },
        {
            "id": "georgia_tech_cs",
            "name": "Georgia Institute of Technology",
            "type": "university",
            "location": "Georgia, USA",
            "description": "Georgia Tech's computer science program is known for its strong industry connections and practical approach. The program covers software engineering, cybersecurity, machine learning, and computer graphics. Students have access to excellent internship and co-op opportunities. The program emphasizes hands-on learning and real-world applications. Good preparation in mathematics and programming is important.",
            "programs": ["Computer Science", "Cybersecurity", "Software Engineering", "Game Design"],
            "gpa_requirement": "3.6",
            "tuition": 12682,
            "acceptance_rate": 0.23,
            "ranking": 8,
            "website": "https://www.cc.gatech.edu",
            "year": 2024
        }
    ]
    
    return colleges

def create_sample_programs():
    """Create sample program-specific data."""
    
    programs = [
        {
            "id": "stanford_ai_masters",
            "name": "Master of Science in Artificial Intelligence",
            "school": "Stanford University",
            "type": "program",
            "location": "California, USA",
            "description": "Stanford's MS in AI program provides deep technical knowledge in artificial intelligence, machine learning, and related fields. Students take courses in machine learning, natural language processing, computer vision, and robotics. The program includes both coursework and research components. Students work with world-class faculty on cutting-edge AI research projects.",
            "degree_type": "Masters",
            "duration": "2 years",
            "gpa_requirement": "3.8",
            "prerequisites": ["Linear Algebra", "Probability", "Programming"],
            "career_outcomes": ["AI Research Scientist", "Machine Learning Engineer", "Data Scientist"],
            "year": 2024
        },
        {
            "id": "mit_robotics_phd",
            "name": "PhD in Robotics",
            "school": "Massachusetts Institute of Technology", 
            "type": "program",
            "location": "Massachusetts, USA",
            "description": "MIT's PhD in Robotics program combines mechanical engineering, electrical engineering, and computer science. Students conduct research in areas like autonomous vehicles, humanoid robots, and medical robotics. The program emphasizes both theoretical foundations and practical implementation. Students work in state-of-the-art laboratories with access to advanced robotic systems.",
            "degree_type": "PhD",
            "duration": "5-6 years",
            "gpa_requirement": "3.7",
            "prerequisites": ["Calculus", "Physics", "Programming", "Control Systems"],
            "career_outcomes": ["Robotics Research Scientist", "Autonomous Systems Engineer", "Professor"],
            "year": 2024
        }
    ]
    
    return programs

def save_sample_data():
    """Save sample data to files."""
    
    # Create directories
    Path("data/sample").mkdir(parents=True, exist_ok=True)
    
    # Create college data
    colleges = create_sample_colleges()
    with open("data/sample/colleges.json", "w") as f:
        json.dump(colleges, f, indent=2)
    
    # Create program data  
    programs = create_sample_programs()
    with open("data/sample/programs.json", "w") as f:
        json.dump(programs, f, indent=2)
    
    # Create combined data for ingestion
    all_data = colleges + programs
    with open("data/sample/combined_data.json", "w") as f:
        json.dump(all_data, f, indent=2)
    
    print(f"✅ Created sample data:")
    print(f"   - {len(colleges)} colleges in data/sample/colleges.json")
    print(f"   - {len(programs)} programs in data/sample/programs.json") 
    print(f"   - {len(all_data)} total items in data/sample/combined_data.json")

def create_training_data():
    """Create sample Q&A data for model training."""
    
    qa_data = [
        {
            "question": "What are the best computer science programs for AI research?",
            "answer": "For AI research, Stanford University and MIT are top choices. Stanford's CS program has a strong focus on AI and machine learning with world-class faculty. MIT's CSAIL lab is one of the largest AI research centers. Both programs offer excellent research opportunities and have produced many AI breakthroughs."
        },
        {
            "question": "Which universities offer good computer science programs with lower tuition?",
            "answer": "UC Berkeley and Georgia Tech offer excellent computer science programs at lower costs. UC Berkeley is ranked #3 nationally with in-state tuition around $14,000. Georgia Tech is ranked #8 with strong industry connections and in-state tuition around $12,000. Both provide excellent value for computer science education."
        },
        {
            "question": "What GPA do I need for top computer science programs?",
            "answer": "Top CS programs are highly competitive. Stanford and Caltech typically require 3.9+ GPA, MIT and CMU around 3.8+, and UC Berkeley around 3.7+. However, GPA is just one factor - research experience, programming projects, and strong letters of recommendation are also crucial for admission."
        },
        {
            "question": "What should I study to prepare for computer science programs?",
            "answer": "Strong preparation in mathematics is essential, including calculus, linear algebra, and discrete mathematics. Programming experience in languages like Python, Java, or C++ is important. Physics can be helpful, especially for programs with hardware components. Taking AP Computer Science or doing programming projects demonstrates your interest and aptitude."
        },
        {
            "question": "What career opportunities are available with a computer science degree?",
            "answer": "CS graduates have diverse career options including software engineer, data scientist, AI/ML engineer, cybersecurity specialist, product manager, and research scientist. Top programs like Stanford, MIT, and Berkeley have excellent industry connections with companies like Google, Apple, Microsoft, and emerging startups."
        }
    ]
    
    # Save training data
    Path("data/training").mkdir(parents=True, exist_ok=True)
    with open("data/training/college_qa.json", "w") as f:
        json.dump(qa_data, f, indent=2)
    
    print(f"✅ Created {len(qa_data)} Q&A pairs in data/training/college_qa.json")

def main():
    """Main function to create all sample data."""
    print("🚀 Creating Sample Data for CollegeAdvisor RAG System")
    print("=" * 55)
    
    save_sample_data()
    create_training_data()
    
    print("\n🎯 Next Steps:")
    print("1. Start ChromaDB server: chroma run --host 0.0.0.0 --port 8000")
    print("2. Ingest data: python -m college_advisor_data.cli ingest --source data/sample/combined_data.json")
    print("3. Test RAG system: python test_rag.py")

if __name__ == "__main__":
    main()

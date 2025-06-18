from test_script import MCQEvaluator  

questions = [  
    "What is 2+2? (A) 3 (B) 4 (C) 5 (D) 6",  
    "Which language is this? (A) Python (B) Java (C) C++ (D) Ruby"  
]  

answers = ["b", "a"]  # Correct options

# Run the test!  
evaluator = MCQEvaluator(model_name="deepseek-r1:8b-llama-distill-q8_0")

# Run evaluation with 30-second timeout per question 
evaluator.run_test(questions, answers, time_limit=30)  
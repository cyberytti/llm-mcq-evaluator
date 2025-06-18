from agno.agent import Agent, RunResponse
from agno.models.ollama import Ollama
from pydantic import BaseModel, Field
from typing import List
import asyncio
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text

class Answer(BaseModel):
    Justification: str = Field(..., description="A brief explanation justifying the selected option.")
    Selected_option: str = Field(..., description="The selected option (A, B, C, or D).")

class MCQEvaluator:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.score_list = []
        self.console = Console()  # Rich console for beautiful output
        self.agent = Agent(
            model=Ollama(id=self.model_name),
            description="You are an expert AI assistant trained to analyze and solve multiple-choice questions (MCQs) accurately across various subjects.",
            instructions=[
                "You will be given a multiple-choice question (MCQ) with four options labeled A to D.",
                "Carefully analyze the question, consider all options, and determine the most appropriate answer.",
                "Provide a brief, subject-relevant justification for the selected answer.",
                "Respond only with the letter (A, B, C, or D) of the selected option and the justification.",
            ],
            markdown=True,
            response_model=Answer
        )

    async def _get_answer(self, question):
        response = await asyncio.to_thread(self.agent.run, question)
        return response.content.Justification, response.content.Selected_option.lower()

    async def _run_test(self, questions: List[str], answers: List[str], time_limit: int):
        # Ensure the logs directory exists
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "test_logs.log")

        # --- Rich UI: Initial Header ---
        header_text = f"[bold]Model:[/] {self.model_name}\n[bold]Total questions:[/] {len(questions)}"
        self.console.print(Panel(header_text, title="[bold cyan]MCQ Test Initialized[/]", expand=False))

        # Write initial log header
        with open(log_file_path, "w") as file:
            file.write(f"""==============
Model name: {self.model_name}
Total questions: {len(questions)}
===============\n\n\n""")
        
        # --- Rich UI: Progress Bar ---
        progress_columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
        ]

        with Progress(*progress_columns, console=self.console) as progress:
            task = progress.add_task("[cyan]Running Test...", total=len(questions))

            for q in range(len(questions)):
                progress.update(task, description=f"[cyan]Solving question {q+1}")
                
                try:
                    explanation, selected_option = await asyncio.wait_for(self._get_answer(questions[q]), timeout=time_limit)
                    
                    status_text = Text(f"Question {q+1}: ")
                    if selected_option == answers[q].lower():
                        self.score_list.append(1)
                        verdict = "Correct"
                        status_text.append("✔ Correct", style="bold green")
                    else:
                        verdict = "Incorrect"
                        status_text.append("❌ Incorrect", style="bold red")
                    
                    self.console.print(status_text)

                except asyncio.TimeoutError:
                    verdict = "Timeout"
                    explanation = "N/A"
                    selected_option = "Timeout"
                    
                    status_text = Text(f"Question {q+1}: ")
                    status_text.append("⏳ Timeout", style="bold yellow")
                    self.console.print(status_text)
                
                # Log detailed results to file (core logic unchanged)
                output_text = f"""Question_number: {q+1}

Question:  
{questions[q]}

AI Response:  
{selected_option}

Correct Answer:  
{answers[q]}

AI Reasoning:  
{explanation}

Final_verdict: 
{verdict}
\n
"""
                with open(log_file_path, "a") as file:
                    file.write(output_text)
                
                progress.advance(task)

        # --- Rich UI: Final Summary ---
        total_questions = len(questions)
        accuracy = (sum(self.score_list) / total_questions * 100) if total_questions > 0 else 0
        
        summary_text = (
            f"Accuracy: [bold green]{accuracy:.2f}%[/]\n\n"
            f"Detailed logs saved to [cyan]{log_file_path}[/]"
        )
        self.console.print(Panel(summary_text, title="[bold cyan]Test Complete[/]", expand=False))

        # Write final score to log file
        with open(log_file_path, "a") as file:
            file.write(f"""\n
=================
TOTAL SCORE: {accuracy:.2f} % accuracy
=================
""")

    def run_test(self, questions: List[str], answers: List[str], time_limit: int):
        # This public method remains unchanged
        asyncio.run(self._run_test(questions, answers, time_limit))
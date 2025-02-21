from typing import List, Optional, Dict
from pathlib import Path
import json
from openai import OpenAI
from tenacity import retry, stop_after_attempt,wait_random_exponential

from principle_alignment.utilities.logger import Logger


class Alignment:
    """A class to handle AI alignment principles and their analysis."""
    
    def __init__(self, client: OpenAI, model: str,verbose: bool = False):
        """
        Initialize the Alignment class.
        
        Args:
            client (OpenAI): OpenAI client instance to use for API requests. Must be initialized.
            model (str): Model name to use for predictions. Must be compatible with the client.
            verbose (bool, optional): Enable verbose logging. Defaults to False.
            
        Raises:
            ValueError: If client is None or model is empty.
            TypeError: If client is not an OpenAI instance or model is not a string.
        """

        if not isinstance(client, OpenAI):
            raise TypeError("client must be an instance of OpenAI")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")

        self.__logger = Logger(verbose=verbose)
        self.__verbose = verbose

        self.principles: List[str] = []
        self.__system_prompt = ""

        self.client = client
        self.model = model
        self.__backup_client = client
        self.__backup_model = model
        
        if self.__verbose:
            self.__logger.log("info", f"Initialized Alignment with model: {model}")

    def prepare(self, 
             principles: Optional[List[str]] = None, 
             principles_file: Optional[str] = None, 
             client: Optional[OpenAI] = None, 
             model: Optional[str] = None) -> None:
        """
        Initialize and configure the Alignment system with principles.

        Loads principles and generates a system prompt for alignment analysis. This method
        handles the complete setup process including principle validation, loading, and 
        system prompt generation.

        The method allows temporary override of the default OpenAI client and model
        during preparation. These settings will be automatically restored after
        the system prompt is generated.
        
        Args:
            principles: List of alignment principles. Each principle must be a non-empty string.
                Takes precedence over principles_file if both are provided.
            principles_file: Path to a text file containing principles (one per line).
                Only used if principles argument is None.
            client: Optional OpenAI client to use temporarily during preparation.
                Will be restored to the default client afterwards.
            model: Optional model name to use temporarily during preparation.
                Will be restored to the default model afterwards.

        Raises:
            ValueError: If neither principles nor principles_file is provided,
                    or if principles contain empty/invalid strings.
            RuntimeError: If principles loading or system prompt generation fails.
            FileNotFoundError: If principles_file doesn't exist.
                        
        Examples:
            Basic usage with direct principles:
            >>> alignment = Alignment(client=OpenAIInstance, model="gpt-4o-mini", verbose=False)
            >>> alignment.prepare(principles=["Do no harm", "Respect user privacy"])

            Loading from a file:
            >>> alignment.prepare(principles_file="principles.txt")

            With temporary client/model override:
            >>> alignment.prepare(
            ...     principles=["Principle 1"],
            ...     client=TemporaryOpenAIInstance,
            ...     model=TemporaryModelName
            ... )
        """

        try:
            # Step 1: Validate input
            if not principles and not principles_file:
                raise ValueError("Either principles or principles_file must be provided")
            
            if principles and not all(isinstance(p, str) and p.strip() for p in principles):
                raise ValueError("All principles must be non-empty strings")

            # Step 2: Load principles
            self.__logger.log("info", "Starting preparation process...")
            self.__load_principles(principles, principles_file)

            if not self.principles:
                raise RuntimeError("Principles were not properly loaded")

            # Step 3: Handle client/model configuration
            if client or model:
                self.__logger.log("info", "Overwriting client/model information for preparation")
                self.__override_client_info(client, model)

            # Step 4: Generate system prompt
            if not self.client:
                raise ValueError("OpenAI client must be set before preparing the system")
                
            self.__logger.log("info", "Generating system prompt...")
            self.__generate_system_prompt()

            if not self.__system_prompt:
                raise RuntimeError("System prompt was not properly generated")

            # Step 5: Restore original client/model if needed
            self.__restore_client_info()

            self.__logger.log(
                "success", 
                "Alignment Agent is ready to analyze user input for principle violations",
                color="bold_green"
            )

        except Exception as e:
            self.__logger.log("error", f"Preparation failed: {str(e)}", color="red")
            raise RuntimeError(f"Preparation failed: {str(e)}")

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def align(self, user_input: str) -> Dict:
        """
        Analyze user input for potential principle violations.
        
        Args:
            user_input: Text to analyze for violations
            
        Returns:
            {
                "is_violation": bool,
                "violated_principle": str | None,
                "explanation": str | None
            }
                
        Raises:
            AlignmentError: When alignment analysis fails
            ValueError: When input validation fails
                
        Note:
            prepare() must be called successfully before using this method. This ensures
            that principles are loaded and the system prompt is generated.
            
        Examples:
            Basic usage:
            >>> alignment = Alignment(client=OpenAIInstance, model="gpt-4")
            >>> alignment.prepare(principles=["Respect privacy", "Do no harm"])
            >>> result = alignment.align("Let's collect user data without consent")
            >>> print(result)
            {
                "is_violation": true,
                "violated_principle": "Respect privacy",
                "explanation": "The suggestion to collect user data without consent..."
            }

            No violation case:
            >>> result = alignment.align("Let's help users improve their productivity")
            >>> print(result)
            {
                "is_violation": false,
                "violated_principle": null,
                "explanation": null
            }
        """
        if not user_input or not isinstance(user_input, str):
            raise ValueError("user_input must be a non-empty string")

        if not self.__system_prompt:
            raise ValueError("System prompt not generated. Make sure you call prepare() before align()")

        try:
            self.__logger.log("info", f"Analyzing input for principle violations: {user_input[:100]}...")
            
            messages = [
                {"role": "system", "content": self.__system_prompt},
                {"role": "user", "content": user_input}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            
            # Log the result
            if result.get("is_violation"):
                self.__logger.log("warning", 
                    f"Violation detected: {result.get('violated_principle', 'Unknown principle')} \n\nExplanation: {result.get('explanation', 'No explanation provided')}",
                    color="purple")
            else:
                self.__logger.log("info", "No violations detected", color="green")
                
            return result

        except json.JSONDecodeError as e:
            self.__logger.log("error", f"Failed to parse API response: {str(e)}", color="red")
            raise RuntimeError(f"Invalid JSON response from API: {str(e)}")
            
        except Exception as e:
            self.__logger.log("error", f"Error during alignment analysis: {str(e)}", color="red")
            raise RuntimeError(f"Alignment analysis failed: {str(e)}")

    def __load_principles(self, 
                       principles: Optional[List[str]] = None, 
                       principles_file: Optional[str] = None) -> None:
        """
        Load principles from either a list or a file.

        Args:
                principles (Optional[List[str]]): A list of alignment principles as strings.
                    Takes precedence over principles_file if both are provided.
                principles_file (Optional[str]): Path to a text file containing principles (one per line).
                    Only used if principles argument is None.

        Raises:
            ValueError: If neither principles nor principles_file is provided, or if principles
                contain empty/invalid strings
            TypeError: If principles is provided but is not a list of strings
            FileNotFoundError: If principles_file is provided but does not exist
            RuntimeError: If there is an error reading from the principles file

        Examples:
            >>> self.__load_principles(principles=["Do no harm"])  # List takes precedence
            >>> self.__load_principles(principles_file="principles.txt")  # File used if no list provided
        """

        # First validate that at least one source is provided
        if principles_file is None and principles is None:
            raise ValueError("Either principles or principles_file must be provided")

        # Handle direct principles list first (takes precedence)
        if principles is not None:
            if not isinstance(principles, list):
                raise TypeError("principles must be a list of strings")
            if any(not isinstance(p, str) or not p.strip() for p in principles):
                raise ValueError("All principles must be non-empty strings")
            self.principles = [p.strip() for p in principles]
            self.__logger.log("info", f"Loaded {len(self.principles)} principles from list")
            return  # Exit early since principles list takes precedence

        # Handle principles file if no direct principles provided
        try:
            file_path = Path(principles_file)
            if not file_path.exists():
                raise FileNotFoundError(f"Principles file not found: {principles_file}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                self.principles = [p.strip() for p in file.read().split('\n') if p.strip()]
            
            if not self.principles:
                raise ValueError("No valid principles found in file")
                
            self.__logger.log("info", 
                            f"Loaded {len(self.principles)} principles from file: {principles_file}")
        
        except Exception as e:
            self.__logger.log("error", f"Error loading principles from file: {str(e)}", color="red")
            raise RuntimeError(f"Error loading principles from file: {str(e)}")

    def __override_client_info(self, client: Optional[OpenAI] = None, model: Optional[str] = None) -> None:
        """
        Override the existing client and model information.
        
        Args:
            client: OpenAI client instance
            model: Model name to use
        """
        if client:
            self.client = client
        if model:
            self.model = model

    def __restore_client_info(self) -> None:
        """Restore the original client and model information."""
        self.client = self.__backup_client
        self.model = self.__backup_model

    def __generate_system_prompt(self) -> None:
        """
        Generate a system prompt for principle violation analysis.

        Args:
            with_examples: Whether to include violation examples in the prompt

        Returns:
            str: Formatted system prompt

        Raises:
            ValueError: If principles is empty or if client is None when with_examples=True
        """
        self.__logger.log("info", "Generating system prompt for principle violation analysis")
        
        if not self.principles:
            self.__logger.log("error", "No principles loaded. Call __load_principles first.",color="red")
            raise ValueError("No principles loaded. Call __load_principles first.")
        
        try:
            violations = []
            self.__logger.log("info", "Generating violations examples for each principle...")
            
            for principle in self.principles:
                self.__logger.log("info", f"Generating violations example for principle:\n\n {principle}",color="bold_blue")
                violations_example = self.__get_violations_example(principle)
                violations_example["principle"] = principle
                violations.append(violations_example)
            
            system_prompt = self.__build_system_prompt(self.principles, violations)
            self.__logger.log("success", "System prompt generated successfully",color="bold_green")
            self.__system_prompt = system_prompt
            
        except Exception as e:
            self.__logger.log("error", f"Error generating system prompt: {str(e)}",color="red")
            raise
        
    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def __get_violations_example(self, principle: str) -> Dict:
        """
        Generate examples of principle violations.

        Args:
            principle: The principle to analyze

        Returns:
            dict: JSON response containing violation examples

        Raises:
            ValueError: If principle is invalid or client is not set
        """
        if not principle or not isinstance(principle, str):
            raise ValueError("principle must be a non-empty string")
        
        if self.client is None:
            raise ValueError("OpenAI client must be set before generating examples")

        user_prompt = self.__build_violations_prompt(principle)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.__logger.log("error", f"Error generating violations example for principle: {principle} - {str(e)}",color="red")
            raise

    def __build_violations_prompt(self, principle: str) -> str:
        """
        Build the prompt for violations example generation.
        
        Args:
            principle: The principle to analyze
            
        Returns:
            str: Formatted prompt
        """
        return f"""
        Based on the three levels of "cognition-decision-behavior" (where behavior includes both language and actions), generate examples that violate the following principle:

        ### PRINCIPLE:
        {principle}

        ### EXAMPLES TYPES:
        thought,decision,sentence,behavior

        ### EXAMPLE JSON OUTPUT:
        {{
            "violations":
            [{{
                "thought": "xxx",
                "decision": "xxx",
                "sentence": "xxx",
                "behavior": "xxx"
            }},
            {{
                "thought": "xxx",
                "decision": "xxx",
                "sentence": "xxx",
                "behavior": "xxx"
            }},
            {{
                "thought": "xxx",
                "decision": "xxx",
                "sentence": "xxx",
                "behavior": "xxx"
            }}]
        }}
        """

    def __build_system_prompt(self, principles: List[str], violations: Optional[List[Dict]] = None) -> str:
        """
        Build the system prompt with optional violations examples.
        
        Args:
            principles: List of principles
            violations: Optional list of violation examples
            
        Returns:
            str: Formatted system prompt
        """
        system_prompt = (
            f"### ROLE:\n\n"
            f"You are an AI assistant trained to identify violations of Provided Principles\n\n"
            f"### PRINCIPLES:\n\n"
            f"{json.dumps(principles, indent=4, ensure_ascii=False)}\n\n"
            f"### VIOLATIONS EXAMPLES:\n\n"
            f"{json.dumps(violations, indent=4, ensure_ascii=False)}\n\n"
            "### TASK:\n\n"
            "Analyze the provided input for potential violations against the defined principles. For each input:\n"
            "1. Evaluate if it violates any principle\n"
            "2. If a violation is found, identify the specific principle and provide a detailed explanation\n"
            "3. Return a standardized JSON response\n\n"
            "### EXAMPLE JSON OUTPUT:\n\n"
            "{\n"
            '    "is_violation": true,\n'
            '    "violated_principle": "xxx",\n'
            '    "explanation": "xxx"\n'
            "}\n\n"
            "or\n\n"
            "{\n"
            '    "is_violation": false,\n'
            '    "violated_principle": null,\n'
            '    "explanation": null\n'
            "}\n\n"
            "### User Input:\n\n"
        )

        return system_prompt
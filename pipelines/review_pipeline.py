from pipeline import Pipeline
import torch
from llmlite.apis import ChatLLM, ChatMessage
from pipelines.pipeline import Pipeline
from pipelines.templates.review_template import (
    REVIEW_USER_PROMPT,
    REVIEW_SYSTEM_PROMPT,
)
from providers.github_provider import get_pr_info
from utils.log import rayserve_logger


class ReviewPipeline(Pipeline):
    """
    ReviewPipeline is used for review the PR.
    """

    def __init__(self,
                 model_name_or_path: str = None,
                 task: str = None,
                 torch_dtype: torch.dtype = torch.float16,
                 ) -> None:
        self.chat = ChatLLM(
            model_name_or_path=model_name_or_path, task=task, torch_dtype=torch_dtype
        )
        self.logger = rayserve_logger()

    def completion(self, url: str) -> str:
        pr_info = get_pr_info(url=url)
        user_prompt = REVIEW_USER_PROMPT.format(
            title=pr_info["title"],
            description=pr_info["description"],
            commit_messages=pr_info["commit_messages"],
            pr_diffs=pr_info["pr_diffs"],
        )

        self.logger.debug("user prompt: {prompt}".format(prompt=user_prompt))

        return self.chat.completion(
            messages=[
                ChatMessage(role="system", content=REVIEW_SYSTEM_PROMPT),
                ChatMessage(role="user", content=user_prompt),
            ],
        )
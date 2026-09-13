"""Register the configured DeepSeek model in MetaGPT's local cost table."""

DEEPSEEK_PRICES = {
    "deepseek-flash": {"prompt": 0.0003, "completion": 0.0012},
    "deepseek-v4-pro": {"prompt": 0.00132, "completion": 0.00396},
}


def register() -> None:
    from metagpt.context import Context
    from metagpt.utils.cost_manager import CostManager
    from metagpt.utils.token_counter import TOKEN_COSTS

    TOKEN_COSTS.update(DEEPSEEK_PRICES)
    CostManager.model_fields["token_costs"].default.update(DEEPSEEK_PRICES)
    Context.model_fields["cost_manager"].default.token_costs.update(DEEPSEEK_PRICES)

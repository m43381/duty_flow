from .matrix_builder import build_matrix
from .matrix_saver import save_matrix
from .ruleset import get_ruleset_for_user, seed_rules


class AccessControlService:
    @staticmethod
    def get_ruleset_for_user(user):
        return get_ruleset_for_user(user)

    @staticmethod
    def seed_rules(user, resource: str):
        return seed_rules(user, resource)

    @staticmethod
    def build_matrix(user, resource: str, level: int):
        return build_matrix(user, resource, level)

    @staticmethod
    def save_matrix(user, resource: str, level: int, post_data):
        return save_matrix(user, resource, level, post_data)
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import require_auth, current_user_id
from .schemas import (
    ContributionSummary,
    PasswordChange,
    SkillsUpdate,
    UserProfile,
    UserUpdate,
)
from .service import (
    change_password,
    contribution_summary,
    get_user,
    set_skills,
    update_profile,
)

blp = Blueprint("users", "users", url_prefix="/api/users", description="用户与个人资料")


@blp.route("/me")
class Me(MethodView):
    @require_auth
    @blp.response(200, UserProfile)
    def get(self):
        return get_user(current_user_id())

    @require_auth
    @blp.arguments(UserUpdate)
    @blp.response(200, UserProfile)
    def patch(self, data):
        return update_profile(current_user_id(), data)


@blp.route("/me/skills")
class Skills(MethodView):
    @require_auth
    @blp.arguments(SkillsUpdate)
    @blp.response(200, SkillsUpdate)
    def put(self, data):
        skills = set_skills(current_user_id(), data["skills"])
        return {"skills": skills}


@blp.route("/me/password")
class Password(MethodView):
    @require_auth
    @blp.arguments(PasswordChange)
    @blp.response(200)
    def put(self, data):
        change_password(current_user_id(), data["current_password"], data["new_password"])
        return {"ok": True}


@blp.route("/me/contribution")
class Contribution(MethodView):
    @require_auth
    @blp.response(200, ContributionSummary)
    def get(self):
        return contribution_summary(current_user_id())


@blp.route("/<int:uid>")
class UserDetail(MethodView):
    @require_auth
    @blp.response(200, UserProfile)
    def get(self, uid):
        return get_user(uid)

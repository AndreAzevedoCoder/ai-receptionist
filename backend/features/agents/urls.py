from django.urls import path

from .views import AgentListCreateView, AgentDetailView, AgentMeView, AgentQuestionsView

urlpatterns = [
    path('', AgentListCreateView.as_view(), name='agent_list_create'),
    path('me/', AgentMeView.as_view(), name='agent_me'),
    path('me/questions/', AgentQuestionsView.as_view(), name='agent_questions'),
    path('<uuid:agent_id>/', AgentDetailView.as_view(), name='agent_detail'),
]

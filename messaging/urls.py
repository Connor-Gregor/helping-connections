from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("thread/<int:thread_id>/", views.thread_detail, name="thread_detail"),
    path("start/<int:user_id>/", views.start_dm, name="start_dm"),
    path("new/", views.new_thread, name="new_thread"),
    path("thread/<int:thread_id>/delete/", views.delete_thread, name="delete_thread"),
    path("delete-all/", views.delete_all_threads, name="delete_all_threads"),
]
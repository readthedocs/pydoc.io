from django.views.generic import TemplateView

from pydoc.taskapp.celery import build


class HomeView(TemplateView):
    template_name = "pages/home.html"
    title = "Pydoc Home"

    def projects(self):
        return [
            # {
            #     'name': 'Django',
            #     'version': '1.9',
            # },
            {
                'name': 'requests',
                'version': '2.9.2',
            },
        ]


class BuildView(TemplateView):
    template_name = "pages/build.html"
    title = "Pydoc Build"

    def build(self):
        build.delay(project='requests', version='2.9.2')

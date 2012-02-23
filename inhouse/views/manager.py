# -*- coding: utf-8 -*-

"""Views for the project managers."""

# TODO: Copy project form
# TODO: Default step assignment
# TODO: Mass editing

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from inhouse import models
from inhouse.forms import ProjectDefaultStepForm
from inhouse.views.utils import render


def default_steps(request, project_id):
    """Assign default project steps to a project.

    :params project_id: Id of the project to be edited
    """
    project = get_object_or_404(models.Project, pk=project_id)
    form = ProjectDefaultStepForm()
    form.set_step_choices()
    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('admin:inhouse_project_change',
                                                args=(project.id,)))
        #if form.is_valid():
        ids = request.POST.getlist('steps')
        if len(ids) == 0:
            messages.warning(request, _(u'No steps have been selected.'))
        else:
            tpls = models.ProjectStepTemplate.objects.filter(id__in=ids)
            for tpl in tpls:
                query = models.ProjectStep.objects.filter(project=project,
                                                          name=tpl.name)
                if query.count() != 0:
                    continue
                new = models.ProjectStep.copy(tpl)
                new.project = project
                new.next_position()
                new.save()
            messages.success(request, _(u'The project steps have been'
                                        u' successfully added.'))
            return HttpResponseRedirect(reverse(
                'admin:inhouse_project_changelist'))
    return render(request, 'admin/inhouse/project/default_steps.html', {
        'form': form, 'project': project})

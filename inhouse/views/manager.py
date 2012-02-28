# -*- coding: utf-8 -*-

"""Views for the project managers."""

# TODO: Copy project form
# TODO: Default step assignment
# TODO: Mass editing

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from inhouse import models
from inhouse.forms import ProjectCopyForm, ProjectDefaultStepForm
from inhouse.views.utils import render


@permission_required('inhouse.add_project')
def copy_project(request, project_id):
    """Creates a copy of a project and optionally of it's child objects.

    :param project_id: The id of the project to be copied
    """
    project = get_object_or_404(models.Project, pk=project_id)
    form = ProjectCopyForm(initial={'name': u'%s \'%s\'' % (_(u'Copy of'),
                                                            project.name)})
    steps = project.projectstep_set.all()
    members = project.projectuser_set.all()
    trackers = project.projecttracker_set.all()
    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('admin:inhouse_project_change',
                                                args=(project.id,)))
        with_steps = bool(request.POST.get('steps'))
        with_members = bool(request.POST.get('members'))
        with_trackers = bool(request.POST.get('tracker'))
        name = request.POST.get('name')
        p = models.Project.copy(project)
        p.name = name
        p.save()
        p.master = p
        p.save()
        if with_steps:
            # Copy the project steps
            #steps = models.ProjectStep.objects.filter(project=project)
            for step in steps:
                new = models.ProjectStep.copy(step)
                new.project = p
                new.next_position()
                new.save()
        if with_members:
            # Copy all project members
            #members = models.ProjectUser.objects.filter(project=project)
            for project_user in members:
                new = models.ProjectUser()
                new.project = p
                new.user = project_user.user
                if project_user.default_step:
                    # Retrieve the user's default step, if possible
                    #query = models.ProjectStep.objects.get_by_name(
                    #    p, project_user.default_step.name)
                    query = models.ProjectStep.objects.filter(
                        project=p, name=project_user.default_step.name)
                    if query.count() == 1:
                        new.default_step = query[0]
                    else:
                        new.default_step = None
                new.save()
        if with_trackers:
            # Copy assigned issue trackers
            #project_trackers = models.ProjectTracker.objects.filter(
                #project=project)
            for project_tracker in trackers:
                new = models.ProjectTracker()
                new.project = p
                new.tracker = project_tracker.tracker
                new.save()
        messages.success(request, _(u'The project has been'
                                    u' successfully copied.'))
        return HttpResponseRedirect(reverse(
            'admin:inhouse_project_changelist'))
    return render(request,
                  'admin/inhouse/project/copy_project.html', {
            'form': form, 'project': project, 'steps': steps,
            'members': members, 'trackers': trackers},)


@permission_required('inhouse.change_project')
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

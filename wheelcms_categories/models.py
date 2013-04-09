from django.db import models
from django import forms

from wheelcms_axle.content import Content

from wheelcms_spokes.page import PageBase, PageType, PageForm
from wheelcms_axle.content import type_registry


class Category(PageBase):
    items = models.ManyToManyField(Content, related_name="categories")
    ## manytomany to content

    def __unicode__(self):
        return self.title

class CategoryForm(PageForm):
    ## exclude categories?

    class Meta(PageForm.Meta):
        model = Category

    items = forms.ModelMultipleChoiceField(queryset=Content.objects.all(),
                                           required=False)

class CategoryType(PageType):
    model = Category
    title = "A category"
    form = CategoryForm

    @classmethod
    def extend_form(cls, f, *args, **kwargs):
        f.fields['categories'] = forms.ModelMultipleChoiceField(
            queryset=Category.objects.all(), required=False)
        if 'instance' in kwargs:
            f.fields['categories'].initial = kwargs['instance'].categories.all()
        f.advanced_fields += ["categories"]

    @classmethod
    def extend_save(cls, form, instance, commit=True):
        old_save_m2m = form.save_m2m

        def save_m2m():
            old_save_m2m()
            instance.categories.clear()
            for cat in form.cleaned_data['categories']:
                instance.categories.add(cat)

        form.save_m2m = save_m2m

type_registry.register(CategoryType, extends=Content)


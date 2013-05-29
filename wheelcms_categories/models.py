from django.db import models
from django import forms

from wheelcms_axle.content import Content
from wheelcms_axle.node import Node

from wheelcms_spokes.page import PageBase, PageType, PageForm
from wheelcms_axle.content import type_registry
from wheelcms_axle.templates import template_registry

from wheelcms_axle.impexp import WheelSerializer

class CategorySerializer(WheelSerializer):
    extra = WheelSerializer.extra + ('items', )

    def serialize_extra_items(self, field, o):
        """ serialize 'items'. Since it's a m2m, field will be a string """
        res = []
        for i in o.items.all():
            res.append(dict(name="item", value=i.node.path))

        return dict(name="items", value=res)

    def deserialize_extra_items(self, extra, tree, model):
        items = []
        for item in tree.findall("items/item"):
            items.append(item.text)

        def delay_items():
            for i in items:
                ## make absolute path relative to basenode. Relative path
                ## may be "" / None which means the root, or (relatively) 
                ## self.basenode
                if not i or i == '/':
                    n = self.basenode
                else:
                    n = self.basenode.child(i.lstrip('/'))
                # import pytest; pytest.set_trace()
                model.items.add(n.content())

        return delay_items

class Category(PageBase):
    items = models.ManyToManyField(Content, related_name="categories")
    ## manytomany to content

    def __unicode__(self):
        return self.title

class CategoryForm(PageForm):

    class Meta(PageForm.Meta):
        model = Category
        exclude = PageForm.Meta.exclude + ["items"]


    #items = forms.ModelMultipleChoiceField(queryset=Content.objects.all(),
    #                                       required=False)

class CategoryType(PageType):
    model = Category
    title = "A category"
    form = CategoryForm

    serializer = CategorySerializer

    add_to_index = False

    @property
    def icon(self):
        ## assume that if this category contains children, they're
        ## categories themselves and this is more a collection of
        ## categories.
        if self.instance.node.children().exists():
            return "categories.png"
        return "category.png"

    @classmethod
    def extend_form(cls, f, *args, **kwargs):
        if f.light:  ## Do not extend light forms
            return
        category_choices = []
        for c in Category.objects.all():
            s = c.spoke()
            w = s.workflow()
            if w.is_published():
                category_choices.append((c.id, c.title))
            else:
                category_choices.append((c.id, "(%s) %s" %
                                        (w.state(),  c.title)))

        f.fields['categories'] = forms.MultipleChoiceField(
                                  choices=category_choices, required=False)
        if 'instance' in kwargs:
            f.fields['categories'].initial = \
               kwargs['instance'].categories.all().values_list("pk", flat=True)
        f.advanced_fields += ["categories"]

    @classmethod
    def extend_save(cls, form, instance, commit=True):
        if form.light:
            return

        old_save_m2m = form.save_m2m

        def save_m2m():
            old_save_m2m()
            instance.categories.clear()
            for cat in form.cleaned_data['categories']:
                instance.categories.add(cat)

        form.save_m2m = save_m2m

type_registry.register(CategoryType, extends=Content)
template_registry.register(CategoryType, "wheelcms_categories/category_view.html",
                           "Blog view", default=True)

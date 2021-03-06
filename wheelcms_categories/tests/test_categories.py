from xml.etree import ElementTree
from wheelcms_axle.impexp import Importer

from wheelcms_axle.content import  type_registry
from wheelcms_axle.tests.models import Type1, Type1Type
from wheelcms_axle.tests.utils import MockedQueryDict

from wheelcms_categories.models import Category, CategoryType

import pytest

@pytest.fixture()
def cat1():
    return Category(title="cat1", state="published").save()

@pytest.fixture()
def cat2():
    return Category(title="cat2", state="published").save()

@pytest.mark.usefixtures("localtyperegistry")
class TestCategories(object):
    """
        Test the categories implementation. More specifically,
        the extending behaviour
    """
    types = (CategoryType, Type1Type)

    def test_noextend(self, client, root):
        """ No extending taking place """
        form = Type1Type.form(parent=root)
        assert 'categories' not in form.fields

    def test_extended_field(self, client, root):
        """ verify that extended content gets a categories formfield """
        type_registry.register(CategoryType, extends=Type1)
        form = Type1Type.form(parent=root)
        assert 'categories' in form.fields

    def test_extended_save(self, client, root, cat1):
        """ We can save the categories """
        type_registry.register(CategoryType, extends=Type1)
        form = Type1Type.form(parent=root,
                              data=MockedQueryDict(title="test",
                                        categories=[cat1.id],
                                        language="en"))
        t = form.save()
        assert list(t.categories.all()) == [cat1]
        assert list(cat1.items.all()) == [t.content_ptr]

    def test_extended_save_nocommit(self, client, root, cat1, cat2):
        """ but nocommit should not alter the categories m2m until it's
            really committed """
        type_registry.register(CategoryType, extends=Type1)
        i = Type1(title="existing").save()
        i.categories = [cat2]

        form = Type1Type.form(parent=root,
                              instance=i,
                              data=MockedQueryDict(title="test",
                                        categories=[cat1.id],
                                        language="en"))
        t = form.save(commit=False)
        assert list(t.categories.all()) == [cat2]
        form.save()
        assert list(t.categories.all()) == [cat1]

from wheelcms_axle.tests.test_spoke import BaseSpokeTest, BaseSpokeTemplateTest
from wheelcms_axle.tests.test_impexp import BaseSpokeImportExportTest

class TestCategorySpokeTemplate(BaseSpokeTemplateTest):
    """ Test the Category type """
    type = CategoryType

    def valid_data(self, **kw):
        """ return additional data for Category validation """
        return MockedQueryDict(body="Hello World", **kw)

    def test_form_excluded_items(self, client, root):
        """ verify certain fields are excluded from the form """
        form = self.type.form(parent=root, data={'template':"bar/foo"})
        assert 'items' not in form.fields

class TestCategorySpoke(BaseSpokeTest):
    """ Test the Category type """
    type = CategoryType

@pytest.mark.usefixtures("localtyperegistry")
class TestCategorySpokeImpExp(BaseSpokeImportExportTest):
    type = CategoryType
    types = (Type1Type, )
    spoke = CategoryType

    def create(self, **kw):
        return self.type.create(**kw).save()

    def test_items_export_import(self, client, root):
        """ add some content to a category, export and import it,
            verify the items survive the roundtrip """

        n1 = root.add("t1")
        n2 = root.add("t2")
        n3 = root.add("t3")

        t1 = Type1(title="target 1", node=n1).save()
        t2 = Type1(title="target 2", node=n2).save()
        t3 = Type1(title="target 3", node=n3).save()

        c = CategoryType.create(title="category").save()
        c.instance.items.add(t1, t2)

        res, files = c.serializer().serialize(c)

        c, delay = self.spoke.serializer().deserialize(self.spoke, res)
        assert delay
        ## run the delays, which will set the m2m relation
        for d in delay:
            d()
        assert t1.content_ptr in c.instance.items.all()
        assert t2.content_ptr in c.instance.items.all()
        assert t3.content_ptr not in c.instance.items.all()

    def test_items_export_import_base(self, client, root):
        """ importing content with categories in a different (non-root)
            base should adjust the category references """

        xml = """<?xml version="1.0" ?>
<site base="" version="1">
 <node>
  <content slug="" type="tests.type1">
    <fields>
      <field name="publication">2013-04-15T09:09:00.615574+00:00</field>
      <field name="created">2013-04-15T09:09:00.615645+00:00</field>
      <field name="meta_type">type1</field>
      <field name="title">Root</field>
      <field name="modified">2013-04-15T09:09:00.615639+00:00</field>
      <field name="state">private</field>
      <field name="expire">2033-04-18T09:09:00.615586+00:00</field>
      <field name="t1field">None</field>
      <field name="template"/>
      <field name="owner"/>
      <field name="navigation">False</field>
      <tags/>
      <field name="description"/>
    </fields>
  </content>
  <children>
   <node>
    <content slug="t1" type="tests.type1">
      <fields>
        <field name="publication">2013-04-15T09:09:00.620481+00:00</field>
        <field name="created">2013-04-15T09:09:00.620544+00:00</field>
        <field name="meta_type">type1</field>
        <field name="title">target 1</field>
        <field name="modified">2013-04-15T09:09:00.620538+00:00</field>
        <field name="state">private</field>
        <field name="expire">2033-04-18T09:09:00.620491+00:00</field>
        <field name="t1field">None</field>
        <field name="template"/>
        <field name="owner"/>
        <field name="navigation">False</field>
        <tags/>
        <field name="description"/>
      </fields>
    </content>
    <children/>
   </node>
   <node>
    <content slug="cat" type="wheelcms_categories.category">
      <fields>
        <field name="title">cat</field>
        <field name="state">published</field>
        <field name="owner"/>
        <field name="navigation">False</field>
        <field name="meta_type">category</field>
        <items>
          <item>/</item>
          <item>/t1</item>
        </items>
      </fields>
    </content>
   </node>
  </children>
 </node>
</site>"""


        base = root.add("sub1").add("sub2")
        tree = ElementTree.fromstring(xml)
        res = Importer(base).run(tree)

        assert isinstance(base.content(), Type1)
        assert len(base.children()) == 2
        cat = base.child("cat")
        cont = base.child("t1")
        items = [x.node for x in cat.content().items.all()]

        assert base in items
        assert cont in items


## class TestCategorySpokeSearch(BaseTestSearch):
##     type = CategoryType
##
## categories are no longer indexed...
from haystack.query import SearchQuerySet

@pytest.mark.usefixtures("localtyperegistry")
class TestCategorySearch(object):
    type = CategoryType

    def test_not_indexed(self):
        self.sqs = SearchQuerySet()

        c = Category(title="cat", description="cat")
        c.save()

        res = self.sqs.auto_query("cat")
        assert not res

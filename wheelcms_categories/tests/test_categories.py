from wheelcms_axle.models import Node
from wheelcms_axle.content import TypeRegistry, type_registry
from wheelcms_axle.tests.models import Type1, Type1Type

from ..models import Category, CategoryType

class TestCategories(object):
    """
        Test the categories implementation. More specifically,
        the extending behaviour
    """
    def setup(self):
        """ replace typeregistry with our local one """
        self.registry = TypeRegistry()
        type_registry.set(self.registry)
        self.cat1 = Category(title="cat1", state="published").save()
        self.cat2 = Category(title="cat2", state="published").save()

    def test_noextend(self, client):
        """ No extending taking place """
        self.registry.register(Type1Type)
        self.registry.register(CategoryType)
        form = Type1Type.form(parent=Node.root())
        assert 'categories' not in form.fields

    def test_extended_field(self, client):
        """ verify that extended content gets a categories formfield """
        self.registry.register(Type1Type)
        self.registry.register(CategoryType, extends=Type1)
        form = Type1Type.form(parent=Node.root())
        assert 'categories' in form.fields

    def test_extended_save(self, client):
        """ We can save the categories """
        self.registry.register(Type1Type)
        self.registry.register(CategoryType, extends=Type1)
        form = Type1Type.form(parent=Node.root(),
                              data=dict(title="test",
                                        categories=[self.cat1.id]))
        t = form.save()
        assert list(t.categories.all()) == [self.cat1]
        assert list(self.cat1.items.all()) == [t.content_ptr]

    def test_extended_save_nocommit(self, client):
        """ but nocommit should not alter the categories m2m until it's
            really committed """
        self.registry.register(Type1Type)
        self.registry.register(CategoryType, extends=Type1)
        i = Type1(title="existing").save()
        i.categories = [self.cat2]

        form = Type1Type.form(parent=Node.root(),
                              instance=i,
                              data=dict(title="test",
                                        categories=[self.cat1.id]))
        t = form.save(commit=False)
        assert list(t.categories.all()) == [self.cat2]
        form.save()
        assert list(t.categories.all()) == [self.cat1]

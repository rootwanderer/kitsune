from nose.tools import eq_, raises

import sumo.models
from taggit.models import Tag

from questions.models import Question, QuestionMetaData, Answer
from questions.tags import add_existing_tag
from questions.tests import TestCaseBase, TaggingTestCaseBase, tags_eq
from questions.question_config import products


class TestAnswer(TestCaseBase):
    """Test the Answer model"""

    def test_new_answer_updates_question(self):
        """Test saving a new answer updates the corresponding question.
        Specifically, last_post and num_replies should update."""
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)
        question.save()

        eq_(0, question.num_answers)
        eq_(None, question.last_answer)

        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")
        answer.save()

        question = Question.objects.get(pk=question.id)
        eq_(1, question.num_answers)
        eq_(answer, question.last_answer)

        question.delete()

    def test_delete_last_answer_of_question(self):
        """Deleting the last_answer of a Question should update the question.
        """
        question = Question.objects.all()[0]
        last_answer = question.last_answer

        # add a new answer and verify last_answer updated
        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")
        answer.save()
        question = Question.objects.get(pk=question.id)

        eq_(question.last_answer.id, answer.id)

        # delete the answer and last_answer should go back to previous value
        answer.delete()
        question = Question.objects.get(pk=question.id)
        eq_(question.last_answer.id, last_answer.id)
        eq_(Answer.objects.filter(pk=answer.id).count(), 0)

    def test_creator_num_posts(self):
        """Test retrieval of post count for creator of a particular answer"""
        question = Question.objects.all()[0]
        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")

        eq_(answer.creator_num_posts, 1)

    def test_creator_num_answers(self):
        """Test retrieval of answer count for creator of a particular answer"""
        question = Question.objects.all()[0]
        answer = Answer(question=question, creator_id=47963,
                        content="Test Answer")
        answer.save()

        question.solution = answer
        question.save()

        eq_(answer.creator_num_answers, 1)

class TestQuestionMetadata(TestCaseBase):
    """Tests handling question metadata"""

    def setUp(self):
        super(TestQuestionMetadata, self).setUp()

        # add a new Question to test with
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=1)
        question.save()
        self.question = question

    def tearDown(self):
        super(TestQuestionMetadata, self).tearDown()

        # remove the added Question
        self.question.delete()

    def test_add_metadata(self):
        """Test the saving of metadata."""
        metadata = {'version': u'3.6.3', 'os': u'Windows 7'}
        self.question.add_metadata(**metadata)
        saved = QuestionMetaData.objects.filter(question=self.question)
        eq_(dict((x.name, x.value) for x in saved), metadata)

    def test_metadata_property(self):
        """Test the metadata property on Question model."""
        self.question.add_metadata(crash_id='1234567890')
        eq_('1234567890', self.question.metadata['crash_id'])

    def test_product_property(self):
        """Test question.product property."""
        self.question.add_metadata(product='desktop')
        eq_(products['desktop'], self.question.product)

    def test_category_property(self):
        """Test question.category property."""
        self.question.add_metadata(product='desktop')
        self.question.add_metadata(category='d1')
        eq_(products['desktop']['categories']['d1'], self.question.category)

    def test_clear_mutable_metadata(self):
        """Make sure it works and clears the internal cache.

        crash_id should get cleared, while product, category, and useragent
        should remain.

        """
        q = self.question
        q.add_metadata(product='desktop', category='d1', useragent='Fyerfocks',
                       crash_id='7')

        q.metadata
        q.clear_mutable_metadata()
        md = q.metadata
        assert 'crash_id' not in md, \
            "clear_mutable_metadata() didn't clear the cached metadata."
        eq_(dict(product='desktop', category='d1', useragent='Fyerfocks'), md)


class QuestionTests(TestCaseBase):
    """Tests for Question model"""

    def test_save_updated(self):
        """Make sure saving updates the `updated` field."""
        q = Question.objects.all()[0]
        updated = q.updated
        q.save()
        self.assertNotEqual(updated, q.updated)

    def test_save_no_update(self):
        """Saving with the `no_update` option shouldn't update `updated`."""
        q = Question.objects.all()[0]
        updated = q.updated
        q.save(no_update=True)
        eq_(updated, q.updated)

    def test_default_manager(self):
        """Assert Question's default manager is SUMO's ManagerBase.

        This is easy to get wrong with taggability.

        """
        eq_(Question._default_manager.__class__, sumo.models.ManagerBase)


class AddExistingTagTests(TaggingTestCaseBase):
    """Tests for the add_existing_tag helper function."""

    def setUp(self):
        super(AddExistingTagTests, self).setUp()
        self.untagged_question = Question.objects.get(pk=1)

    def test_tags_manager(self):
        """Make sure the TaggableManager exists.

        Full testing of functionality is a matter for taggit's tests.

        """
        tags_eq(self.untagged_question, [])

    def test_add_existing_case_insensitive(self):
        """Assert add_existing_tag works case-insensitively."""
        add_existing_tag('LEMON', self.untagged_question.tags)
        tags_eq(self.untagged_question, [u'lemon'])

    @raises(Tag.DoesNotExist)
    def test_add_existing_no_such_tag(self):
        """Assert add_existing_tag doesn't work when the tag doesn't exist."""
        add_existing_tag('nonexistent tag', self.untagged_question.tags)

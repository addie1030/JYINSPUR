# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestTags(TransactionCase):

    def test_create_tag(self):
        marketing_assets = self.ref('documents.documents_marketing_assets_facet')
        tag = self.env['documents.tag'].create({
            'name': 'Foo',
            'facet_id': marketing_assets,
        })
        self.assertEqual(tag.facet_id.id, marketing_assets, 'should have the right facet')
        self.assertEqual(tag.name, 'Foo', 'should have the right name')
        self.assertTrue(tag.sequence > 0, 'should have a non-zero sequence')

    def test_name_get(self):
        facet_assets = self.env['documents.facet'].browse(self.ref('documents.documents_marketing_assets_facet'))
        tag_assets_ads = self.env['documents.tag'].browse(self.ref('documents.documents_marketing_assets_ads'))
        self.assertEqual(tag_assets_ads.name_get(), [(tag_assets_ads.id, '%s > %s' % (facet_assets.name, tag_assets_ads.name))], 'should return formatted name containing facet name')

    def test_group_by_documents(self):
        folder_id = self.ref('documents.documents_marketing_folder')
        facet_assets = self.env['documents.facet'].browse(self.ref('documents.documents_marketing_assets_facet'))
        tag_assets_ads = self.env['documents.tag'].browse(self.ref('documents.documents_marketing_assets_ads'))
        tag_assets_videos = self.env['documents.tag'].browse(self.ref('documents.documents_marketing_assets_Videos'))

        tags = self.env['documents.tag'].group_by_documents(folder_id)
        self.assertEqual(len(tags), 5, 'should return a non-empty list of tags')

        first_record = {
            'facet_id': facet_assets.id,
            'facet_name': facet_assets.name,
            'facet_sequence': facet_assets.sequence,
            'facet_tooltip': None,
            'tag_id': tag_assets_ads.id,
            'tag_name': tag_assets_ads.name,
            'tag_sequence': tag_assets_ads.sequence,
            '__count': 1,
        }
        self.assertEqual(tags[0], first_record, 'first record should match')

        last_record = {
            'facet_id': facet_assets.id,
            'facet_name': facet_assets.name,
            'facet_sequence': facet_assets.sequence,
            'facet_tooltip': None,
            'tag_id': tag_assets_videos.id,
            'tag_name': tag_assets_videos.name,
            'tag_sequence': tag_assets_videos.sequence,
            '__count': 0,
        }
        self.assertEqual(tags[-1], last_record, 'last record should match')

    def test_group_by_documents_reordered(self):
        folder_id = self.ref('documents.documents_marketing_folder')
        facet_assets = self.env['documents.facet'].browse(self.ref('documents.documents_marketing_assets_facet'))
        tag_assets_images = self.env['documents.tag'].browse(self.ref('documents.documents_marketing_assets_images'))
        tag_assets_videos = self.env['documents.tag'].browse(self.ref('documents.documents_marketing_assets_Videos'))

        tag_assets_images.sequence = 1

        tags = self.env['documents.tag'].group_by_documents(folder_id)
        self.assertEqual(len(tags), 5, 'should return a non-empty list of tags')

        first_record = {
            'facet_id': facet_assets.id,
            'facet_name': facet_assets.name,
            'facet_sequence': facet_assets.sequence,
            'facet_tooltip': None,
            'tag_id': tag_assets_images.id,
            'tag_name': tag_assets_images.name,
            'tag_sequence': tag_assets_images.sequence,
            '__count': 2,
        }
        self.assertEqual(tags[0], first_record, 'first record should match')

        last_record = {
            'facet_id': facet_assets.id,
            'facet_name': facet_assets.name,
            'facet_sequence': facet_assets.sequence,
            'facet_tooltip': None,
            'tag_id': tag_assets_videos.id,
            'tag_name': tag_assets_videos.name,
            'tag_sequence': tag_assets_videos.sequence,
            '__count': 0,
        }
        self.assertEqual(tags[-1], last_record, 'last record should match')

    def test_group_by_documents_empty_folder(self):
        empty_folder_id = self.ref('documents.documents_marketing_brand1_folder')
        facet_assets = self.env['documents.facet'].browse(self.ref('documents.documents_marketing_assets_facet'))
        tag_assets_ads = self.env['documents.tag'].browse(self.ref('documents.documents_marketing_assets_ads'))
        tag_assets_videos = self.env['documents.tag'].browse(self.ref('documents.documents_marketing_assets_Videos'))
        tags = self.env['documents.tag'].group_by_documents(empty_folder_id)

        self.assertEqual(len(tags), 5, 'should return a non-empty list of tags')

        first_record = {
            'facet_id': facet_assets.id,
            'facet_name': facet_assets.name,
            'facet_sequence': facet_assets.sequence,
            'facet_tooltip': None,
            'tag_id': tag_assets_ads.id,
            'tag_name': tag_assets_ads.name,
            'tag_sequence': tag_assets_ads.sequence,
            '__count': 0,
        }
        self.assertEqual(tags[0], first_record, 'first record should match')

        last_record = {
            'facet_id': facet_assets.id,
            'facet_name': facet_assets.name,
            'facet_sequence': facet_assets.sequence,
            'facet_tooltip': None,
            'tag_id': tag_assets_videos.id,
            'tag_name': tag_assets_videos.name,
            'tag_sequence': tag_assets_videos.sequence,
            '__count': 0,
        }
        self.assertEqual(tags[-1], last_record, 'last record should match')
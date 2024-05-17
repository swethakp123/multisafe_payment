# -*- coding: utf-8 -*-
{
    'name': "Multi Safe Pay Payment Provider",
    'version': '17.0.1.0.0',
    'depends': ['account','website','website_sale'],
    'category': '',
    'description': """
    Purchase limit for the customer
    """,
    'data': [
            # 'views/payment_provider_views.xml',
            # 'views/payment_template.xml',
            # 'data/payment_method_data.xml',
            # 'data/payment_provider_data.xml',

             ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'application': 'True',
    'installable': True,
}
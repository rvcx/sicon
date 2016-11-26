#!/usr/bin/env python
# -*- coding: utf8 -*-
"""Copy files in an AWS S3 bucket to simulate HTTP content negotation.
"""

__url__ = "http://v.cx/2016/s3-content-negotiation"
__author__ = "Rob Shearer"
__copyright__ = """
Copyright (c) 2016 Rob Shearer. All right reserved.

Redistribution and use of this software, in source and binary forms, with or
without modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

  * Neither the name of the author nor the names of its contributors may be
    used to endorse or promote products derived from this software without
    specific prior written permission.

This software might contain bugs. There might be bugs that stop it from doing
what it was designed to do. There might be bugs that make it do unexpected
things. Potentially catastrophic things. Anyone who uses this software does so
at their own risk; the authors take no responsibility for the results.
"""

__version__ = '0.1.0'
__version_info__ = (0, 1, 0)
__changelog__ = {
    (0, 1, 0) : {
        'released' : (2016, 11, 26),
        'comment' : "Initial release",
    },
}

import argparse
import boto3
import re
import sys

def preferred_path(paths):
    for p in paths:
        if p.endswith('.html'):
            return p
    print('choosing arbitrarily among [{}]'.format(', '.join(paths)))
    return paths[0]


def shadows(paths):
    s = {}
    exp = re.compile(r'(.+)\.[a-zA-Z0-9]+')
    for p in paths:
        m = exp.match(p)
        if m:
            n = m.group(1)
            if n in s:
                s[n] = preferred_path([s[n], p])
            else:
                s[n] = p
    for k, v in s.items():
        yield (k, v)


def main(argv=None):
    version = ( "SiCoN version " + __version__ + " by " + __author__ +
                "\n\nFor more information visit <" + __url__ + ">.\n" +
                __copyright__ )
    usage = '%prog [options] [FILE...]'
    description = \
"""Copy files in an AWS S3 bucket to simulate HTTP content negotiation."""
    try:
        parser = argparse.ArgumentParser(
            description=description, version=version, usage=usage
        )
        parser.add_argument('-b', '--aws-bucket',
            help='use AWS S3 bucket named BUCKET', metavar='BUCKET',
            required=True)
        args = parser.parse_args()

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(args.aws_bucket)
        files = set(obj.key for obj in bucket.objects.all())
        for shadow_key, original_key in shadows(files):
            shadow = s3.Object(bucket.name, shadow_key)
            if shadow_key in files and 'sicon' not in shadow.metadata:
                continue  # don't overwrite "real" files
            original = s3.Object(bucket.name, original_key)
            metadata = dict(original.metadata)
            metadata['sicon'] = 'generated'

            # As far as I can tell, if you change the custom metadata then you
            # must also overwrite all the system metadata as well, which is split
            # across a bunch of attributes and parameters. This is clearly
            # ridiculous.
            other_metadata = {}
            for attr, arg in [('cache_control', 'CacheControl'),
                              ('content_disposition', 'ContentDisposition'),
                              ('content_encoding', 'ContentEncoding'),
                              ('content_language', 'ContentLanguage'),
                              ('content_type', 'ContentType'),
                              ('expires', 'Expires')]:
                if getattr(original, attr) is not None:
                    other_metadata[arg] = getattr(original, attr)
            shadow.copy_from(CopySource={'Bucket':bucket.name,
                                         'Key':original_key},
                             Metadata=metadata, MetadataDirective='REPLACE',
                             **other_metadata)
                             

    except Exception, e:
        raise
        print >>sys.stderr, e
        return 2

if __name__ == '__main__': sys.exit(main())

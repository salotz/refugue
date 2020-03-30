


# pre-made common combinations of the options, not really necessary
# except for some explanation
SYNC_SPECS = (

    ('safe',
     "Safe mode that won't delete or overwrite anything except old files on beta.",
     (
         ('inject', False),
         ('clobber', False),
         ('clean', False),
         ('prune', False),
     ),
    ),

    ('inplace-safe',
     "Safe mode that only changes existing files on beta and doesn't add any new ones.",
     (
         ('inject', True),
         ('clobber', False),
         ('clean', False),
         ('prune', False),
     ),
    ),

    ('inplace',
     "Only updates existing files on beta but ignores modification times.",
     (
         ('inject', True),
         ('clobber', True),
         ('clean', False),
         ('prune', False),
     ),
    ),

    ('update',
     "Most common. Update anything with old modification remove deleted files.",
     (
         ('inject', False),
         ('clobber', False),
         ('clean', True),
         ('prune', False),
     ),
    ),

    ('force-update',
     "Same as 'update' but ignores modification times.",
     (
         ('inject', False),
         ('clobber', True),
         ('clean', True),
         ('prune', False),
     ),
    ),

    ('colonize',
     "Nuclear option. Ignores modification times, replicate deletes, "
     "and get rid of any excluded file in replica.",
     (
         ('inject', False),
         ('clobber', True),
         ('clean', True),
         ('prune', True),
     ),
    ),
)

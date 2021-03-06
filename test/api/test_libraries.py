from base import api

from .helpers import (
    LibraryPopulator,
    TestsDatasets,
    wait_on_state
)


class LibrariesApiTestCase( api.ApiTestCase, TestsDatasets ):

    def setUp( self ):
        super( LibrariesApiTestCase, self ).setUp()
        self.library_populator = LibraryPopulator( self )

    def test_create( self ):
        data = dict( name="CreateTestLibrary" )
        create_response = self._post( "libraries", data=data, admin=True )
        self._assert_status_code_is( create_response, 200 )
        library = create_response.json()
        self._assert_has_keys( library, "name" )
        assert library[ "name" ] == "CreateTestLibrary"

    def test_delete( self ):
        library = self.library_populator.new_library( "DeleteTestLibrary" )
        create_response = self._delete( "libraries/%s" % library[ "id" ], admin=True )
        self._assert_status_code_is( create_response, 200 )
        library = create_response.json()
        self._assert_has_keys( library, "deleted" )
        assert library[ "deleted" ] is True
        # Test undeleting
        data = dict( undelete='true' )
        create_response = self._delete( "libraries/%s" % library[ "id" ], data=data, admin=True )
        library = create_response.json()
        self._assert_status_code_is( create_response, 200 )
        assert library[ "deleted" ] is False

    def test_nonadmin( self ):
        # Anons can't create libs
        data = dict( name="CreateTestLibrary" )
        create_response = self._post( "libraries", data=data, admin=False, anon=True )
        self._assert_status_code_is( create_response, 403 )
        # Anons can't delete libs
        library = self.library_populator.new_library( "AnonDeleteTestLibrary" )
        create_response = self._delete( "libraries/%s" % library[ "id" ], admin=False, anon=True )
        self._assert_status_code_is( create_response, 403 )
        # Anons can't update libs
        data = dict( name="ChangedName", description="ChangedDescription", synopsis='ChangedSynopsis' )
        create_response = self._patch( "libraries/%s" % library[ "id" ], data=data, admin=False, anon=True )
        self._assert_status_code_is( create_response, 403 )

    def test_update( self ):
        library = self.library_populator.new_library( "UpdateTestLibrary" )
        data = dict( name='ChangedName', description='ChangedDescription', synopsis='ChangedSynopsis' )
        create_response = self._patch( "libraries/%s" % library[ "id" ], data=data, admin=True )
        self._assert_status_code_is( create_response, 200 )
        library = create_response.json()
        self._assert_has_keys( library, 'name', 'description', 'synopsis' )
        assert library['name'] == 'ChangedName'
        assert library['description'] == 'ChangedDescription'
        assert library['synopsis'] == 'ChangedSynopsis'

    def test_create_private_library_permissions( self ):
        library = self.library_populator.new_library( "PermissionTestLibrary" )
        library_id = library[ "id" ]
        role_id = self.library_populator.user_private_role_id()
        self.library_populator.set_permissions( library_id, role_id )
        create_response = self._create_folder( library )
        self._assert_status_code_is( create_response, 200 )

    def test_create_dataset( self ):
        library = self.library_populator.new_private_library( "ForCreateDatasets" )
        payload, files = self.library_populator.create_dataset_request( library, file_type="txt", contents="create_test" )
        create_response = self._post( "libraries/%s/contents" % library[ "id" ], payload, files=files )
        self._assert_status_code_is( create_response, 200 )
        library_datasets = create_response.json()
        assert len( library_datasets ) == 1
        library_dataset = library_datasets[ 0 ]

        def show():
            return self._get( "libraries/%s/contents/%s" % ( library[ "id" ], library_dataset[ "id" ] ) )

        wait_on_state( show, assert_ok=True )
        library_dataset = show().json()
        self._assert_has_keys( library_dataset, "peek", "data_type" )
        assert library_dataset[ "peek" ].find("create_test") >= 0
        assert library_dataset[ "file_ext" ] == "txt", library_dataset[ "file_ext" ]

    def _create_folder( self, library ):
        create_data = dict(
            folder_id=library[ "root_folder_id" ],
            create_type="folder",
            name="New Folder",
        )
        return self._post( "libraries/%s/contents" % library[ "id" ], data=create_data )

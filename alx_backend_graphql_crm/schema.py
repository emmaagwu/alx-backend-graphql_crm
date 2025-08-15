import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
    """
    Root Query class that combines all app queries.
    Currently pulling from crm.schema.Query
    """
    pass


class Mutation(CRMMutation, graphene.ObjectType):
    """
    Root Mutation class that combines all app mutations.
    Currently pulling from crm.schema.Mutation
    """
    pass


schema = graphene.Schema(
    query=Query,
    mutation=Mutation
)

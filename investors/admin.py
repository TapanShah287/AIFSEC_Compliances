from django.contrib import admin
from .models import Investor, KYCStatus, FATCADeclaration, InvestorDocument, CommunicationLog, InvestorBankAccount
admin.site.register(Investor)
admin.site.register(KYCStatus)
admin.site.register(FATCADeclaration)
admin.site.register(InvestorDocument)
admin.site.register(CommunicationLog)
admin.site.register(InvestorBankAccount)

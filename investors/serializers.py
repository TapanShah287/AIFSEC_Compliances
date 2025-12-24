from rest_framework import serializers
from .models import Investor, InvestorDocument

class InvestorDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the 2025 compliant Document Vault.
    """
    class Meta:
        model = InvestorDocument
        fields = '__all__'

class InvestorSerializer(serializers.ModelSerializer):
    """
    Complete serializer for the Investor model.
    Updated for 2025 to include Demat, Accreditation, and Financial Properties.
    """
    # Read-only properties for the dashboard
    total_committed = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_contributed = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    uncalled_commitment = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    
    # Nested documents for the detail view
    documents = InvestorDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Investor
        fields = '__all__'
        # Ensure unique fields like PAN and Email return clear 400 errors
        # if duplicates are attempted.
        extra_kwargs = {
            'email': {'required': True},
            'pan': {'required': True},
            'accreditation_expiry': {'allow_null': True, 'required': False},
            'demat_account_no': {'allow_null': True, 'required': False},
            'dp_id': {'allow_null': True, 'required': False},
        }

    def to_internal_value(self, data):
        """
        Interprets empty strings as None for nullable fields.
        This prevents 400 errors when HTML forms send "" for date/optional fields.
        """
        # Create a mutable copy of the data if it's a QueryDict (standard for Django forms)
        if hasattr(data, 'dict'):
            data = data.dict()
        
        nullable_fields = ['accreditation_expiry', 'demat_account_no', 'dp_id', 'phone']
        for field in nullable_fields:
            if field in data and data[field] == "":
                data[field] = None
        
        return super().to_internal_value(data)

    def validate_pan(self, value):
        """Standard 10-digit PAN validation."""
        if value and len(value) != 10:
            raise serializers.ValidationError("PAN must be exactly 10 characters.")
        return value.upper()
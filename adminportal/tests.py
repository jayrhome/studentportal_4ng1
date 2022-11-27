from django.test import TestCase
from . models import *
from django.contrib.auth import get_user_model
import json
from datetime import date, datetime

User = get_user_model()


def convert_qs(obj):
    return obj


def make_students():
    user_list = [
        ["aai@gmail.com", "Aai", "aaigmail"],
        ["ssi@gmail.com", "Ssi", "ssigmail"],
        ["ddi@gmail.com", "Ddi", "ddigmail"],
        ["ffi@gmail.com", "Ffi", "ffigmail"],
        ["ggi@gmail.com", "Ggi", "ggigmail"],
    ]

    try:
        for item in user_list:
            userobj = User.objects.create_user(
                email=item[0],
                display_name=item[1],
                password=item[2]
            )
            userobj.is_active = True
            userobj.save()

        user_dict = User.objects.values('email', 'display_name').filter(
            is_student=True, is_active=True)

        user_dict1 = list(map(convert_qs, user_dict))

        return print(json.dumps(user_dict1, indent=2, separators=(",", "=")))
    except Exception as e:
        return e


def make_shs_track():
    track = [
        ["Academic Track", """The Academic Track has four strands:
        a. Accountancy, Business and Management (ABM) Strand
        b. Science, Technology, Engineering, and Mathematics (STEM) Strand
        c. Humanities and Social Science (HUMSS) Strand and
        d. General Academic Strand (GAS)"""],
        ["Arts and Design Track", """The Arts and Design Track covers a wide range of art forms: Theater, Music, Dance, Creative Writing, Visual Arts, and Media Arts. Prior to enrollment, there is art/creative talent assessment and guidance to gauge a student’s art inclination and aptitude. The track has six general or common subjects that focus on acquiring competencies required for further specialization in the different artistic areas."""],
        ["Technical-Vocational-Livelihood (TVL) Track", """The SHS program has a Technical-Vocational-Livelihood (TVL) Track, which has four strands: Agri-Fishery Arts, Home Economics (HE), Information and Communication Technology (ICT), and Industrial Arts. These are aligned with Technology and Livelihood Education (TLE) in Grades 7-10. Each TVL strand offers various specializations that may or may not have a National Certificate (NC) equivalent from TESDA. The time allocation per strand specialization is based on TESDA Training Regulations-Based Courses and is only indicative since the standard time allotment of 80 hours per semester per subject will still be applied. Therefore, each strand specialization must be designed to fit into the 80-hour blocks of time."""],
    ]

    try:
        for item in track:
            track_create = shs_track.objects.create(
                track_name=item[0],
                definition=item[1],
            )
        trackobj = shs_track.objects.all()
        return trackobj
    except Exception as e:
        return e


def make_admission():
    try:
        adm_details = [
            "Lorem",
            "I.",
            "Ipsum",
            "F",
            date.today(),
            "Metro Manila",
            "Filipino",

            "Elem School",
            "Elem Address Quezon City",
            "NCR",
            date.today(),
            True,
            date.today(),
            False,
            date.today(),
            "NCR Learning Center",
            "NCR Quezon City",

            "jhs School",
            "jhs Address Quezon City",
            "NCR",
            date.today(),
            True,
            date.today(),
            False,
            date.today(),
            "NCR Learning Center",
            "NCR Quezon City",

            True,
        ]

        stud_user = User.objects.filter(is_student=True, is_active=True)
        sy = school_year.objects.latest("date_created")
        s1 = shs_strand.objects.get(id=1)
        s2 = shs_strand.objects.get(id=2)

        for user in stud_user:
            student_admission_details.objects.create(
                admission_owner=user,
                first_name=adm_details[0],
                middle_name=adm_details[1],
                last_name=adm_details[2],
                sex=adm_details[3],
                date_of_birth=adm_details[4],
                birthplace=adm_details[5],
                nationality=adm_details[6],

                elem_name=adm_details[7],
                elem_address=adm_details[8],
                elem_region=adm_details[9],
                elem_year_completed=adm_details[10],
                elem_pept_passer=adm_details[11],
                elem_pept_date_completion=adm_details[12],
                elem_ae_passer=adm_details[13],
                elem_ae_date_completion=adm_details[14],
                elem_community_learning_center=adm_details[15],
                elem_clc_address=adm_details[16],

                jhs_name=adm_details[17],
                jhs_address=adm_details[18],
                jhs_region=adm_details[19],
                jhs_year_completed=adm_details[20],
                jhs_pept_passer=adm_details[21],
                jhs_pept_date_completion=adm_details[22],
                jhs_ae_passer=adm_details[23],
                jhs_ae_date_completion=adm_details[24],
                jhs_community_learning_center=adm_details[25],
                jhs_clc_address=adm_details[26],

                is_validated=adm_details[27],
                admission_sy=sy,
                first_chosen_strand=s1,
                second_chosen_strand=s2,
            )
        return student_admission_details.objects.filter(admission_sy=sy)
    except Exception as e:
        return e
